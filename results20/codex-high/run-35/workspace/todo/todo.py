#!/usr/bin/env python3
"""todo - a tiny, dependency-free task manager that lives in Markdown.

Tasks are stored in a single Markdown file (default ~/.todo.md), so your
tasks stay human-readable, portable, and diffable in git.

Each line is rendered as:

    - [ ] (medium) [work] Buy groceries (due 2026-08-05)
              ^priority  ^tag        ^due date

Usage:
    todo add "Buy groceries" --priority high --tag work --due 2026-08-05
    todo list [--tag T] [--all]
    todo done <index>
    todo rm <index>
    todo edit <index> "new text"
"""

from __future__ import annotations

import argparse
import datetime as dt
import os
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path

DEFAULT_FILE = Path("~/.todo.md").expanduser()
PRIORITIES = {"high": 0, "medium": 1, "low": 2}
PRIORITY_COLORS = {"high": "\033[91m", "medium": "\033[93m", "low": "\033[92m"}
RESET = "\033[0m"
RED = "\033[91m"
GREEN = "\033[92m"
YELLOW = "\033[93m"

TASK_RE = re.compile(
    r"^- \[(?P<done>[ xX])\]"
    r"(?:\s+\((?P<priority>high|medium|low)\))?"
    r"(?P<tags>(?:\s+\[[^\]]+\])*)"
    r"(?:\s+\(due\s+(?P<due>\d{4}-\d{2}-\d{2})\))?"
    r"\s+(?P<text>.+)$"
)


@dataclass
class Task:
    text: str
    priority: str = "medium"
    tags: list[str] = field(default_factory=list)
    due: str | None = None
    done: bool = False

    def to_line(self) -> str:
        bits = [f"- [{'x' if self.done else ' '}]"]
        bits.append(f"({self.priority})")
        bits.extend(f"[{t}]" for t in self.tags)
        if self.due:
            bits.append(f"(due {self.due})")
        bits.append(self.text)
        return " ".join(bits)

    @classmethod
    def from_line(cls, line: str) -> "Task | None":
        m = TASK_RE.match(line)
        if not m:
            return None
        tags = re.findall(r"\[([^\]]+)\]", m.group("tags") or "")
        return cls(
            text=m.group("text"),
            priority=m.group("priority") or "medium",
            tags=tags,
            due=m.group("due"),
            done=m.group("done").strip().lower() == "x",
        )


def load(file: Path) -> list[Task]:
    tasks: list[Task] = []
    if not file.exists():
        return tasks
    for line in file.read_text().splitlines():
        task = Task.from_line(line)
        if task:
            tasks.append(task)
    return tasks


def save(tasks: list[Task], file: Path) -> None:
    file.parent.mkdir(parents=True, exist_ok=True)
    file.write_text("\n".join(t.to_line() for t in tasks) + ("\n" if tasks else ""))


def _priority_color(task: Task) -> str:
    return PRIORITY_COLORS.get(task.priority, "")


def _render_task(idx: int, task: Task, plain: bool = False) -> str:
    if plain:
        status = "x" if task.done else " "
        tag_str = "".join(f"[{t}]" for t in task.tags)
        due = f" (due {task.due})" if task.due else ""
        return f"{idx:>3}. [{status}] ({task.priority}) {tag_str}{due} {task.text}"
    box = GREEN + "[x]" + RESET if task.done else "[ ]"
    pri = _priority_color(task) + f"({task.priority})" + RESET
    tags = "".join(f"[{t}]" for t in task.tags)
    due = YELLOW + f"(due {task.due})" + RESET if task.due else ""
    text = task.text if task.done else task.text
    marker = "  " if task.priority == "medium" else ""
    return f"{idx:>3}. {box} {pri} {tags} {due} {marker}{text}"


def _exact_index(raw: str, file: Path) -> int:
    try:
        idx = int(raw)
    except ValueError:
        sys.exit(f"{RED}error:{RESET} '{raw}' is not a number")
    if idx < 1 or idx > len(load(file)):
        sys.exit(f"{RED}error:{RESET} index out of range: {raw}")
    return idx


def cmd_list(args, file: Path) -> None:
    tasks = load(file)
    if args.all:
        shown = list(enumerate(tasks, 1))
    else:
        shown = [(i + 1, t) for i, t in enumerate(tasks) if not t.done]
    if args.tag:
        shown = [(i, t) for i, t in shown if args.tag in t.tags]
    # Sort: priority, then due date (undated last), then insertion order.
    def key(item):
        _, t = item
        due = dt.date.fromisoformat(t.due) if t.due else dt.date.max
        return (PRIORITIES[t.priority], due if due != dt.date.max else dt.date.max)
    shown.sort(key=key)
    # Re-index after filtering/sorting.
    lines = [_render_task(i, t, plain=args.plain) for i, (_, t) in enumerate(shown, 1)]
    if not lines:
        suffix = f" with tag [{args.tag}]" if args.tag else ""
        print(f"No tasks{suffix}.")
        return
    print("\n".join(lines))
    open_count = sum(1 for _, t in shown if not t.done)
    if not args.all:
        print(f"\n{open_count} open task(s).")


def cmd_add(text, args, file: Path) -> None:
    if not text:
        sys.exit(f"{RED}error:{RESET} task text is required")
    tag_list = [t.strip("[]") for t in (args.tags or [])]
    task = Task(
        text=text,
        priority=args.priority,
        tags=[t for t in tag_list if t],
        due=args.due,
    )
    tasks = load(file)
    tasks.append(task)
    save(tasks, file)
    print(f"{GREEN}added:{RESET} {task.text}  [index {len(tasks)}]")


def cmd_done(raw, file: Path) -> None:
    i = _exact_index(raw, file)
    tasks = load(file)
    tasks[i - 1].done = True
    save(tasks, file)
    print(f"{GREEN}done:{RESET} {tasks[i - 1].text}")


def cmd_rm(raw, file: Path) -> None:
    i = _exact_index(raw, file)
    tasks = load(file)
    removed = tasks.pop(i - 1)
    save(tasks, file)
    print(f"{RED}removed:{RESET} {removed.text}")


def cmd_edit(raw, new_text, file: Path) -> None:
    i = _exact_index(raw, file)
    if not new_text:
        sys.exit(f"{RED}error:{RESET} new text is required")
    tasks = load(file)
    tasks[i - 1].text = new_text
    save(tasks, file)
    print(f"{GREEN}edited:{RESET} {new_text}")


def main(argv=None) -> None:
    argv = sys.argv[1:] if argv is None else argv
    parser = argparse.ArgumentParser(
        prog="todo",
        description="A tiny Markdown-based task manager.",
    )
    parser.add_argument("--file", type=lambda p: Path(os.path.expanduser(p)), default=DEFAULT_FILE,
                        help="task file path (default: ~/.todo.md)")
    sub = parser.add_subparsers(dest="cmd", required=True)

    p_add = sub.add_parser("add", help="add a task")
    p_add.add_argument("text", nargs="+", help="task text")
    p_add.add_argument("--priority", choices=PRIORITIES, default="medium")
    p_add.add_argument("--tag", action="append", dest="tags", help="tag (repeatable)")
    p_add.add_argument("--due", help="due date YYYY-MM-DD")
    p_add.set_defaults(func=lambda a: cmd_add(" ".join(a.text), a, a._file))

    p_list = sub.add_parser("list", help="list tasks")
    p_list.add_argument("--all", action="store_true", help="include completed tasks")
    p_list.add_argument("--tag", help="filter by tag")
    p_list.add_argument("--plain", action="store_true", help="disable colors")
    p_list.set_defaults(func=lambda a: cmd_list(a, a._file))

    p_done = sub.add_parser("done", help="mark a task done by index")
    p_done.add_argument("index")
    p_done.set_defaults(func=lambda a: cmd_done(a.index, a._file))

    p_rm = sub.add_parser("rm", help="remove a task by index")
    p_rm.add_argument("index")
    p_rm.set_defaults(func=lambda a: cmd_rm(a.index, a._file))

    p_edit = sub.add_parser("edit", help="rewrite a task's text by index")
    p_edit.add_argument("index")
    p_edit.add_argument("text", nargs="+")
    p_edit.set_defaults(func=lambda a: cmd_edit(a.index, " ".join(a.text), a._file))

    args = parser.parse_args(argv)
    args._file = args.file
    args.func(args)


if __name__ == "__main__":
    main()
