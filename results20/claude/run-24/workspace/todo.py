#!/usr/bin/env python3
"""todo — a small, zero-dependency CLI task manager.

Store tasks in a single JSON file. Add, list, complete, remove, and filter
them by priority, project, and due date. Data lives in ~/.todo/tasks.json by
default (override with $TODO_FILE or --file)."""

from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import sys
import textwrap
from pathlib import Path

__version__ = "1.0.0"

PRIORITIES = ("low", "medium", "high")

DEFAULT_FILE = Path(os.environ.get("TODO_FILE", "~/.todo/tasks.json")).expanduser()

# We track whether this run is from a TTY to pick colors vs plain output.
USE_COLOR = sys.stdout.isatty() and os.environ.get("NO_COLOR") is None


class Style:
    """ANSI escape wrappers. No-ops when color is disabled."""

    def __init__(self, on: bool):
        self.on = on

    def _wrap(self, code: str, text: str) -> str:
        return f"\033[{code}m{text}\033[0m" if self.on else text

    def reset(self, s: str) -> str:
        return self._wrap("0", s)

    def bold(self, s: str) -> str:
        return self._wrap("1", s)

    def dim(self, s: str) -> str:
        return self._wrap("2", s)

    def green(self, s: str) -> str:
        return self._wrap("32", s)

    def red(self, s: str) -> str:
        return self._wrap("31", s)

    def yellow(self, s: str) -> str:
        return self._wrap("33", s)

    def cyan(self, s: str) -> str:
        return self._wrap("36", s)

    def grey(self, s: str) -> str:
        return self._wrap("90", s)


st = Style(USE_COLOR)

PRIORITY_COLOR = {
    "high": lambda s: st.red(st.bold(s)),
    "medium": lambda s: st.yellow(s),
    "low": lambda s: st.grey(s),
}


class TodoError(Exception):
    """Raised for user-facing errors (bad ids, invalid input)."""


class Task:
    __slots__ = ("id", "text", "done", "priority", "project", "due")

    def __init__(self, text, priority="medium", project=None, due=None, id=None, done=False):
        self.id = id
        self.text = text
        self.done = done
        self.priority = priority if priority in PRIORITIES else "medium"
        self.project = project
        self.due = due  # ISO date string "YYYY-MM-DD" or None

    # -- (de)serialization -------------------------------------------------
    def to_dict(self):
        return {
            "id": self.id,
            "text": self.text,
            "done": self.done,
            "priority": self.priority,
            "project": self.project,
            "due": self.due,
        }

    @classmethod
    def from_dict(cls, d):
        return cls(
            text=d["text"],
            priority=d.get("priority", "medium"),
            project=d.get("project"),
            due=d.get("due"),
            id=d.get("id"),
            done=bool(d.get("done", False)),
        )

    # -- sorting / display helpers -----------------------------------------
    PRIORITY_RANK = {"high": 0, "medium": 1, "low": 2}

    def sort_key(self):
        # Overdue items among open tasks sort first (lower rank = earlier).
        overdue = 0 if (self.due and not self.done and self.due < dt.date.today().isoformat()) else 1
        return (overdue, self.PRIORITY_RANK[self.priority], self.due or "9999", self.id or 0)


class TodoStore:
    """Load/save the task list to a JSON file, one run at a time (CLI model)."""

    def __init__(self, path: Path):
        self.path = path

    def load(self) -> list[Task]:
        if not self.path.exists():
            return []
        try:
            data = json.loads(self.path.read_text())
        except (json.JSONDecodeError, OSError) as e:
            raise TodoError(f"Could not read {self.path}: {e}")
        tasks = [Task.from_dict(d) for d in data.get("tasks", [])]
        # mtime-aware ordering is unnecessary; keep insertion order, tag new ids.
        return tasks

    def save(self, tasks: list[Task]):
        self.path.parent.mkdir(parents=True, exist_ok=True)
        payload = {"version": 1, "tasks": [t.to_dict() for t in tasks]}
        # Write atomically so a crash never leaves a half-written file.
        tmp = self.path.with_suffix(".json.tmp")
        tmp.write_text(json.dumps(payload, indent=2) + "\n")
        os.replace(tmp, self.path)


def next_id(tasks: list[Task]) -> int:
    return (max((t.id for t in tasks if t.id is not None), default=0) or 0) + 1


def parse_due(raw: str):
    """Accept 'today'/'tomorrow' or an ISO date; return ISO string or None."""
    if not raw:
        return None
    today = dt.date.today()
    if raw == "today":
        return today.isoformat()
    if raw == "tomorrow":
        return (today + dt.timedelta(days=1)).isoformat()
    try:
        dt.date.fromisoformat(raw)
    except ValueError:
        raise TodoError(f"Bad due date {raw!r} (use YYYY-MM-DD, 'today', or 'tomorrow')")
    return raw


def render_task(t: Task, index: int, show_id: bool) -> str:
    check = "✔" if t.done else " "
    box = st.green(check) if t.done else st.dim(" ")
    line = f"{st.dim('[')}{box}{st.dim(']')} "

    body = t.text if t.done else (PRIORITY_COLOR[t.priority](t.text))
    if t.done:
        body = st.dim(body)
    line += body

    tags = []
    if t.project:
        tags.append(st.cyan(t.project))
    if t.due:
        overdue = not t.done and t.due < dt.date.today().isoformat()
        color = st.red if overdue else st.grey
        tags.append(color("due " + t.due + (" (overdue)" if overdue else "")))
    if tags:
        line += "  " + st.dim(" · ".join(tags))

    if show_id:
        line += f"  {st.dim('#')}{st.grey(index)}"
    return line


def cmd_add(store, args) -> int:
    tasks = store.load()
    task = Task(
        text=args.text,
        priority=args.priority,
        project=args.project,
        due=parse_due(args.due),
        id=next_id(tasks),
    )
    tasks.append(task)
    store.save(tasks)
    n_open = sum(1 for t in tasks if not t.done)
    print(f"{st.green('✔')} Added {st.bold(str('#') + str(task.id))}: {task.text}")
    if n_open:
        print(f"  {st.dim(f'{n_open} open task(s) · {len(tasks)} total')} ")
    return 0


def cmd_list(store, args) -> int:
    tasks = store.load()
    if args.project:
        tasks = [t for t in tasks if t.project == args.project]
    if args.priority:
        tasks = [t for t in tasks if t.priority == args.priority]

    if args.all:
        shown = tasks
    else:
        shown = [t for t in tasks if not t.done]
    shown.sort(key=lambda t: t.sort_key())

    if not shown:
        print("Nothing to do." if not args.all else "No tasks to show.")
        return 0

    print(f"{st.bold('To do')} ({len(shown)} task{'s' if len(shown) != 1 else ''}):")
    for i, t in enumerate(shown, 1):
        print("  " + render_task(t, i, args.all))

    done = sum(1 for t in tasks if t.done)
    if done and not args.all:
        print()
        print(st.dim(f"  {done} completed. Use --all to see them, or `done` to review."))
    return 0


def _resolve(store, raw_id, tasks) -> Task:
    try:
        iid = int(raw_id)
    except ValueError:
        raise TodoError(f"Bad task id {raw_id!r} (expected a number)")
    for t in tasks:
        if t.id == iid:
            return t
    raise TodoError(f"No task with id {iid}")


def cmd_done(store, args) -> int:
    tasks = store.load()
    t = _resolve(store, args.id, tasks)
    t.done = True
    store.save(tasks)
    print(f"{st.green('✔')} Completed {st.bold(f'#{t.id}')} · {st.dim(t.text)}")
    return 0


def cmd_remove(store, args) -> int:
    tasks = store.load()
    t = _resolve(store, args.id, tasks)
    if not args.yes:
        print(f"Remove {st.bold(f'#{t.id}')} · {t.text}? " + st.dim("[y/N] "), end="", flush=True)
        answer = sys.stdin.readline().strip().lower()
        if answer not in ("y", "yes"):
            print("Aborted.")
            return 1
    tasks = [x for x in tasks if x.id != t.id]
    store.save(tasks)
    print(f"Removed {st.bold(f'#{t.id}')}.")
    return 0


def cmd_clear(store, args) -> int:
    tasks = store.load()
    if args.yes:
        keep = tasks
    else:
        print("This permanently deletes ALL tasks. " + st.dim("[y/N] "), end="", flush=True)
        answer = sys.stdin.readline().strip().lower()
        if answer not in ("y", "yes"):
            print("Aborted.")
            return 1
        keep = tasks
    if args.done:
        keep = [t for t in keep if not t.done]
    elif args.all:
        keep = []
    store.save(keep)
    print(f"Cleared. {len(keep)} task(s) remain.")
    return 0


def cmd_parse(args) -> int:
    tasks = store_from_args(args).load()
    return 0


def store_from_args(args):
    path = Path(args.file).expanduser() if args.file else DEFAULT_FILE
    return TodoStore(path)


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="todo",
        description="A small, zero-dependency CLI task manager.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=textwrap.dedent(
            """\
            examples:
              todo add "ship the release" -p high
              todo add "water plants" --project home --due tomorrow
              todo                 # list open tasks
              todo --all           # include completed ones
              todo done 3          # mark #3 complete
              todo list --project work --priority high
            """
        ),
    )
    p.add_argument("-f", "--file", help="path to the tasks JSON file (default: ~/.todo/tasks.json)")
    p.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    sub = p.add_subparsers(dest="command", metavar="COMMAND")

    s_add = sub.add_parser("add", help="add a task")
    s_add.add_argument("text", help='task text, e.g. "write the report"')
    s_add.add_argument("-p", "--priority", choices=PRIORITIES, default="medium", help="priority (default: medium)")
    s_add.add_argument("--project", help="project tag")
    s_add.add_argument("-d", "--due", help="due date: YYYY-MM-DD, 'today', or 'tomorrow'")
    s_add.set_defaults(func=cmd_add)

    s_list = sub.add_parser("list", help="list tasks (default command)")
    s_list.add_argument("-a", "--all", action="store_true", help="include completed tasks")
    s_list.add_argument("--project", help="filter by project")
    s_list.add_argument("-p", "--priority", choices=PRIORITIES, help="filter by priority")
    s_list.set_defaults(func=cmd_list)

    s_done = sub.add_parser("done", help="mark a task complete")
    s_done.add_argument("id", help="task id")
    s_done.set_defaults(func=cmd_done)

    s_rm = sub.add_parser("remove", help="remove a task")
    s_rm.add_argument("id", help="task id")
    s_rm.add_argument("-y", "--yes", action="store_true", help="skip confirmation")
    s_rm.set_defaults(func=cmd_remove)

    s_clear = sub.add_parser("clear", help="remove tasks")
    s_clear.add_argument("-y", "--yes", action="store_true", help="skip confirmation")
    s_clear.add_argument("-d", "--done", action="store_true", help="only clear completed tasks")
    s_clear.add_argument("-a", "--all", action="store_true", help="clear everything (default with -y)")
    s_clear.set_defaults(func=cmd_clear)

    return p


SUBCMDS = ("add", "list", "done", "remove", "clear")


def _default_to_list(argv):
    """A bare `todo` (or `todo -f file`) lists open tasks.

    Global flags like -f/--file precede the subcommand, so insert `list`
    after any leading global-flag/value pair.
    """
    i = 0
    while i < len(argv) and argv[i] in ("-f", "--file"):
        i += 2  # skip the flag and its value
    return argv[:i] + ["list"] + argv[i:]


def main(argv=None) -> int:
    parser = build_parser()
    if argv is None:
        argv = sys.argv[1:]
    # Peel off the subcommand; if none is given, assume `list`.
    # (Except for --version / -h, which are main-parser options.)
    tokens = [t for t in argv if t not in ("-f", "--file")]
    has_meta = any(t in ("--version", "-h", "--help") for t in tokens)
    if not has_meta and not any(t in SUBCMDS for t in tokens):
        argv = _default_to_list(argv)
    args = parser.parse_args(argv)
    store = store_from_args(args)
    try:
        return args.func(store, args)
    except TodoError as e:
        print(f"{st.red('error')}: {e}", file=sys.stderr)
        return 1
    except KeyboardInterrupt:
        print()
        return 130


if __name__ == "__main__":
    sys.exit(main())
