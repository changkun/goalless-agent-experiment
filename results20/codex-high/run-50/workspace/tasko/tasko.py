#!/usr/bin/env python3
"""Tasko — a tiny, dependency-free command-line task manager.

Store, organize, and track tasks with priorities, due dates, tags, and
completion status, all in a single JSON file.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from dataclasses import dataclass
from datetime import date, datetime
from pathlib import Path

APP_NAME = "tasko"
DATA_FILE = Path(os.environ.get("TASKO_FILE", "~/.tasko.json")).expanduser()

PRIORITIES = {"low": 0, "normal": 1, "high": 2}
PRIORITY_EMOJI = {"low": "🟢", "normal": "🟡", "high": "🔴"}

# ANSI helpers (auto-disabled when not a TTY)
COLORS_ENABLED = hasattr(sys.stdout, "isatty") and sys.stdout.isatty()


def c(code: str, text: str) -> str:
    if not COLORS_ENABLED:
        return text
    return f"\033[{code}m{text}\033[0m"


BOLD = lambda s: c("1", s)
DIM = lambda s: c("2", s)
GREEN = lambda s: c("32", s)
RED = lambda s: c("31", s)
YELLOW = lambda s: c("33", s)
CYAN = lambda s: c("36", s)


class TaskoError(Exception):
    """Raised for user-facing errors (bad input, etc.)."""


@dataclass
class Task:
    id: int
    title: str
    priority: str = "normal"
    due: str | None = None
    tags: list[str] | None = None
    done: bool = False
    created: str = ""

    @classmethod
    def from_dict(cls, d: dict) -> "Task":
        return cls(
            id=int(d["id"]),
            title=d["title"],
            priority=d.get("priority", "normal"),
            due=d.get("due"),
            tags=list(d.get("tags", [])),
            done=bool(d.get("done", False)),
            created=d.get("created", ""),
        )

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "title": self.title,
            "priority": self.priority,
            "due": self.due,
            "tags": self.tags or [],
            "done": self.done,
            "created": self.created,
        }


class Store:
    """Read/write the task list to a JSON file."""

    def __init__(self, path: Path = DATA_FILE):
        self.path = path

    def load(self) -> list[Task]:
        if not self.path.exists():
            return []
        try:
            raw = json.loads(self.path.read_text())
        except json.JSONDecodeError as exc:
            raise TaskoError(f"Corrupt data file {self.path}: {exc}")
        tasks = [Task.from_dict(d) for d in raw]
        return sorted(tasks, key=lambda t: t.id)

    def save(self, tasks: list[Task]) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        tmp = self.path.with_suffix(".tmp")
        tmp.write_text(json.dumps([t.to_dict() for t in tasks], indent=2))
        tmp.replace(self.path)


def now_stamp() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M")


def parse_due(value: str) -> str:
    """Accept YYYY-MM-DD, 'today', 'tomorrow', or next weekday."""
    v = value.strip().lower()
    today = date.today()
    if v == "today":
        return today.isoformat()
    if v == "tomorrow":
        return (today.replace(day=today.day + 1)).isoformat()
    # weekday names -> next occurrence
    weekdays = ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]
    if v in weekdays:
        target = weekdays.index(v)
        delta = (target - today.weekday()) % 7
        return (today.replace(day=today.day + delta)).isoformat()
    try:
        return datetime.strptime(value, "%Y-%m-%d").date().isoformat()
    except ValueError:
        raise TaskoError(
            f"Invalid due date: {value!r}. Use YYYY-MM-DD, 'today', 'tomorrow', or a weekday."
        )


def next_id(tasks: list[Task]) -> int:
    return max((t.id for t in tasks), default=0) + 1


def find_task(tasks: list[Task], task_id: int) -> Task:
    for t in tasks:
        if t.id == task_id:
            return t
    raise TaskoError(f"No task with id {task_id}")


def render_due(due: str | None) -> str:
    if not due:
        return DIM("—")
    try:
        when = date.fromisoformat(due)
    except ValueError:
        return DIM(due)
    days = (when - date.today()).days
    if days < 0:
        return RED(f"{due} (overdue)")
    if days == 0:
        return YELLOW(f"{due} (today)")
    if days == 1:
        return (f"{due} (tomorrow)")
    return f"{due}"


def format_tags(tags: list[str]) -> str:
    if not tags:
        return ""
    return " " + " ".join(f"{CYAN('#' + t)}" for t in tags)


def print_header(tasks: list[Task]) -> None:
    total = len(tasks)
    done = sum(1 for t in tasks if t.done)
    open_n = total - done
    overdue = sum(1 for t in tasks if not t.done and t.due and date.fromisoformat(t.due) < date.today())
    summary = [
        f"Total: {BOLD(str(total))}",
        f"Open: {BOLD(str(open_n))}",
        f"Done: {GREEN(str(done))}",
    ]
    if overdue:
        summary.append(f"Overdue: {RED(str(overdue))}")
    print("  ".join(summary))
    if total:
        pct = round(done / total * 100)
        bar_len = 20
        filled = round(bar_len * done / total)
        bar = GREEN("█" * filled) + DIM("░" * (bar_len - filled))
        print(f"  Progress {bar} {pct}%")


def cmd_add(tasks: list[Task], args) -> None:
    task = Task(
        id=next_id(tasks),
        title=args.title,
        priority=args.priority,
        due=parse_due(args.due) if args.due else None,
        tags=args.tags,
        created=now_stamp(),
    )
    tasks.append(task)
    print(f"Added task {BOLD(str(task.id))}: {task.title}")
    if task.due:
        print(f"  Due: {render_due(task.due)}")


def cmd_list(tasks: list[Task], args) -> None:
    filtered = list(tasks)
    if args.status == "done":
        filtered = [t for t in filtered if t.done]
    elif args.status == "open":
        filtered = [t for t in filtered if not t.done]
    if args.priority:
        filtered = [t for t in filtered if t.priority == args.priority]
    if args.tag:
        filtered = [t for t in filtered if args.tag in (t.tags or [])]
    if not args.all and not args.status:
        filtered = [t for t in filtered if not t.done]

    sort_key = {
        "id": lambda t: t.id,
        "priority": lambda t: (PRIORITIES[t.priority], -t.id),
        "due": lambda t: (t.due or "9999-99-99", t.id),
    }[args.sort]
    filtered.sort(key=sort_key)

    print_header(tasks)
    print()
    if not filtered:
        print(DIM("Nothing to show."))
        return
    for t in filtered:
        mark = GREEN("✔") if t.done else DIM("☐")
        star = PRIORITY_EMOJI[t.priority]
        done_mark = DIM("") if not t.done else ""
        print(f"  {mark} {BOLD(str(t.id)):>3}  {star} {t.title}{format_tags(t.tags or [])}")
        if args.verbose:
            line = f"        priority={t.priority}  created={t.created}"
            if t.due:
                line += f"  due={render_due(t.due)}"
            print(DIM(line))


def cmd_done(tasks: list[Task], args) -> None:
    task = find_task(tasks, args.id)
    task.done = True
    print(f"{GREEN('Done:')} {task.title}")


def cmd_undo(tasks: list[Task], args) -> None:
    task = find_task(tasks, args.id)
    task.done = False
    print(f"Reopened: {task.title}")


def cmd_delete(tasks: list[Task], args) -> None:
    task = find_task(tasks, args.id)
    tasks.remove(task)
    print(f"Deleted task {BOLD(str(task.id))}: {task.title}")


def cmd_clear(tasks: list[Task], args) -> None:
    if args.done:
        before = len(tasks)
        tasks[:] = [t for t in tasks if not t.done]
        print(f"Cleared {before - len(tasks)} completed task(s).")
    else:
        tasks.clear()
        print("Cleared all tasks.")


def cmd_priority(tasks: list[Task], args) -> None:
    task = find_task(tasks, args.id)
    task.priority = args.priority
    print(f"Set priority of task {BOLD(str(task.id))} to {PRIORITY_EMOJI[args.priority]} {args.priority}")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog=APP_NAME,
        description="A tiny, dependency-free CLI task manager.",
    )
    parser.add_argument("--file", help=f"Data file (default: {DATA_FILE})")
    sub = parser.add_subparsers(dest="command", required=True)

    p_add = sub.add_parser("add", help="Add a new task")
    p_add.add_argument("title")
    p_add.add_argument("-p", "--priority", choices=PRIORITIES.keys(), default="normal")
    p_add.add_argument("-d", "--due", help="YYYY-MM-DD, 'today', 'tomorrow', or weekday")
    p_add.add_argument("-t", "--tag", action="append", dest="tags", default=[], help="Tag (repeatable)")

    p_list = sub.add_parser("list", aliases=["ls"], help="List tasks")
    p_list.add_argument("-s", "--status", choices=["open", "done"], help="Filter by status")
    p_list.add_argument("-p", "--priority", choices=PRIORITIES.keys(), help="Filter by priority")
    p_list.add_argument("-t", "--tag", help="Filter by tag")
    p_list.add_argument("--sort", choices=["id", "priority", "due"], default="id", help="Sort order")
    p_list.add_argument("-a", "--all", action="store_true", help="Show all tasks, including done")
    p_list.add_argument("-v", "--verbose", action="store_true", help="Show extra detail")

    p_done = sub.add_parser("done", help="Mark a task completed")
    p_done.add_argument("id", type=int)

    p_undo = sub.add_parser("undo", help="Reopen a completed task")
    p_undo.add_argument("id", type=int)

    p_del = sub.add_parser("delete", aliases=["rm"], help="Delete a task")
    p_del.add_argument("id", type=int)

    p_clear = sub.add_parser("clear", help="Clear tasks")
    p_clear.add_argument("--done", action="store_true", help="Only clear completed tasks")

    p_prio = sub.add_parser("priority", help="Change a task's priority")
    p_prio.add_argument("id", type=int)
    p_prio.add_argument("priority", choices=PRIORITIES.keys())

    args = parser.parse_args(argv)

    store = Store(Path(args.file).expanduser() if args.file else DATA_FILE)
    tasks = store.load()

    try:
        if args.command in ("add",):
            cmd_add(tasks, args)
        elif args.command in ("list", "ls"):
            cmd_list(tasks, args)
        elif args.command == "done":
            cmd_done(tasks, args)
        elif args.command == "undo":
            cmd_undo(tasks, args)
        elif args.command in ("delete", "rm"):
            cmd_delete(tasks, args)
        elif args.command == "clear":
            cmd_clear(tasks, args)
        elif args.command == "priority":
            cmd_priority(tasks, args)
        else:
            parser.print_help()
            return 0
    except TaskoError as exc:
        print(f"{RED('Error:')} {exc}", file=sys.stderr)
        return 1

    # Persist on any command that mutates state
    if args.command != "list":
        store.save(tasks)
    return 0


if __name__ == "__main__":
    sys.exit(main())
