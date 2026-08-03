"""A minimal interactive TUI for the todo app (no external dependencies).

Provides a simple command prompt with a live, always-visible task list.
Commands:

    a  <title> | add <title>      add a task (optionally: p=high due=YYYY-MM-DD)
    l | list                      refresh / show the list
    d <id> | done <id>            mark done
    u <id> | undo <id>            mark open
    e <id> ...                    edit a task (--title / --priority / --due)
    rm <id> | del <id>            delete a task
    clear                         remove completed tasks
    q | quit | exit               leave
"""
from __future__ import annotations

import shlex
import sys

from .store import PRIORITIES, TodoError
from .store import Store, sort_key, format_task


HELP_TEXT = """Commands:
  a  <title>           add a task            (e.g. a  Buy milk)
  a  <title> p=high    ... with a priority   (low|normal|high)
  a  <title> due=DATE  ... with a due date   (YYYY-MM-DD)
  d <id> | done <id>   mark a task done
  u <id> | undo <id>   mark a task open
  e <id> [k=v ...]     edit (title / priority / due)
  rm <id> | del <id>   delete a task
  clear                remove all completed tasks
  ls                   refresh the task list
  help                 show this help
  q | quit | exit      leave
"""


def _read(prompt: str) -> str:
    try:
        return input(prompt).strip()
    except EOFError:
        return "quit"


def _parse_add(line: str) -> tuple[str, dict]:
    """Parse 'title [p=high] [due=DATE]' into (title, kwargs)."""
    tokens = shlex.split(line)
    fields = {"priority": None, "due": None}
    title_parts = []
    for token in tokens:
        if token.lower().startswith("p=") and fields["priority"] is None:
            fields["priority"] = token.split("=", 1)[1].lower()
        elif token.lower().startswith("due=") and fields["due"] is None:
            fields["due"] = token.split("=", 1)[1]
        else:
            title_parts.append(token)
    title = " ".join(title_parts).strip()
    return title, {k: v for k, v in fields.items() if v is not None}


def _parse_edit(tokens: list[str]) -> dict:
    fields: dict[str, str | None] = {}
    remaining = []
    for token in tokens:
        if token.startswith("title="):
            fields["title"] = token.split("=", 1)[1]
        elif token.startswith("priority="):
            fields["priority"] = token.split("=", 1)[1].lower()
        elif token.startswith("due="):
            fields["due"] = token.split("=", 1)[1]
        elif token == "no-due":
            fields["due"] = ""
        elif token.startswith("--"):
            pass
        else:
            remaining.append(token)
    if remaining:
        fields["title"] = " ".join(remaining)
    return fields


def _render_list(store: Store, color: bool) -> None:
    tasks = sorted(store.list_all(), key=sort_key)
    if not tasks:
        sys.stdout.write("  (no tasks)\n")
        return
    for task in tasks:
        mark = "[x]" if task.get("done") else "[ ]"
        if color and task.get("done"):
            mark = f"\033[32m{mark}\033[0m"
        title = task.get("title", "")
        if color and task.get("done"):
            title = f"\033[9m{title}\033[0m"
        row = f"  {task.get('id'):>3} {mark} {title}"
        tags = []
        if task.get("priority") != "normal":
            tags.append(f"({task.get('priority')})")
        if task.get("due"):
            Due = task["due"]
            overdue = not task.get("done") and Due < _today()
            suffix = f"due {Due}" + ("  OVERDUE" if overdue else "")
            if color and overdue:
                suffix = f"\033[31m{suffix}\033[0m"
            tags.append(suffix)
        if tags:
            row += "  " + " ".join(tags)
        sys.stdout.write(row + "\n")
    sys.stdout.flush()


def _today() -> str:
    from datetime import date
    return date.today().isoformat()


def run_interactive(store: Store, color: bool = True) -> int:
    sys.stdout.write("== terminal todo ==  (type 'help' for commands)\n")
    _render_list(store, color)
    while True:
        line = _read("> ")
        if not line:
            continue
        parts = line.split(None, 1)
        cmd = parts[0].lower()
        rest = parts[1] if len(parts) > 1 else ""
        tokens = shlex.split(rest) if rest else []
        try:
            if cmd in ("q", "quit", "exit"):
                sys.stdout.write("bye!\n")
                return 0
            elif cmd in ("a", "add"):
                title, kwargs = _parse_add(rest)
                if not title:
                    sys.stdout.write("  (usage) a <title> [p=high] [due=DATE]\n")
                    continue
                task = store.add(title, **kwargs)
                sys.stdout.write(f"  added #{task['id']}\n")
            elif cmd in ("d", "done"):
                store.set_done(int(tokens[0]), True)
            elif cmd in ("u", "undo"):
                store.set_done(int(tokens[0]), False)
            elif cmd in ("rm", "del"):
                store.delete(int(tokens[0]))
            elif cmd == "clear":
                n = store.clear_done()
                sys.stdout.write(f"  cleared {n} task(s)\n")
            elif cmd in ("list", "ls"):
                pass
            elif cmd == "edit" and tokens:
                fields = _parse_edit(tokens[1:])
                store.update(int(tokens[0]), **fields)
            elif cmd == "help":
                sys.stdout.write(HELP_TEXT)
            else:
                sys.stdout.write("  unknown command (try 'help')\n")
                continue
            _render_list(store, color)
        except (TodoError, ValueError, IndexError) as exc:
            sys.stdout.write(f"  error: {exc}\n")
    return 0
