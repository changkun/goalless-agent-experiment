"""Command-line interface for the terminal todo app.

Usage:
    python -m todo_app.cli add "Buy milk" [--priority high] [--due 2026-08-10]
    python -m todo_app.cli list [--done|--open]
    python -m todo_app.cli done 3
    python -m todo_app.cli undo 3
    python -m todo_app.cli edit 3 --title "New title" [--priority low] [--due 2026-09-01]
    python -m todo_app.cli rm 3
    python -m todo_app.cli clear
    python -m todo_app.cli --file tasks.json ...
"""
from __future__ import annotations

import argparse
import sys

from .store import (
    PRIORITIES,
    TodoError,
    Store,
    format_task,
    sort_key,
)


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="todo",
        description="A tiny terminal task manager.",
    )
    parser.add_argument("--file", "-f", default=None, help="path to the task file")
    parser.add_argument("--no-color", action="store_true", help="disable colored output")

    sub = parser.add_subparsers(dest="command", required=True)

    p_add = sub.add_parser("add", help="add a new task")
    p_add.add_argument("title")
    p_add.add_argument("--priority", choices=PRIORITIES, default=None)
    p_add.add_argument("--due", default=None, help="due date as YYYY-MM-DD")

    def add_list_flags(parser: argparse.ArgumentParser) -> None:
        group = parser.add_mutually_exclusive_group()
        group.add_argument("--done", action="store_true", help="only completed tasks")
        group.add_argument("--open", action="store_true", help="only open tasks")

    p_list = sub.add_parser("list", help="list tasks")
    add_list_flags(p_list)
    p_ls = sub.add_parser("ls", help="alias for list", description="alias for list")
    p_ls.set_defaults(command="list")
    add_list_flags(p_ls)

    p_done = sub.add_parser("done", help="mark a task done")
    p_done.add_argument("id", type=int)
    p_undo = sub.add_parser("undo", help="mark a task open again")
    p_undo.add_argument("id", type=int)

    p_edit = sub.add_parser("edit", help="edit a task")
    p_edit.add_argument("id", type=int)
    p_edit.add_argument("--title", default=None)
    p_edit.add_argument("--priority", choices=PRIORITIES, default=None)
    p_edit.add_argument("--due", default=None, help="due date as YYYY-MM-DD")
    p_edit.add_argument("--no-due", action="store_true", help="clear the due date")

    p_rm = sub.add_parser("rm", help="delete a task")
    p_rm.add_argument("id", type=int)

    sub.add_parser("clear", help="remove all completed tasks")
    sub.add_parser("interactive", help="launch an interactive TUI")

    return parser


def _green(text: str) -> str:
    return f"\033[32m{text}\033[0m"


def _red(text: str) -> str:
    return f"\033[31m{text}\033[0m"


def _stroke(text: str) -> str:
    return f"\033[9m{text}\033[0m"


def _display_task(task: dict, color: bool) -> str:
    line = format_task(task)
    if not color:
        return line
    if task.get("done"):
        return _green(_stroke(line))
    if "overdue" in line:
        return line.replace("(overdue)", _red("(overdue)"))
    if task.get("priority") == "high":
        return _red(line)
    return line


def _print_tasks(tasks: list[dict], color: bool) -> None:
    if not tasks:
        sys.stdout.write("No tasks.\n")
        return
    for task in sorted(tasks, key=sort_key):
        sys.stdout.write(_display_task(task, color) + "\n")


def main(argv: list[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)
    color = not args.no_color and sys.stdout.isatty()
    store = Store(args.file) if args.file else Store()
    try:
        if args.command == "add":
            task = store.add(args.title, priority=args.priority, due=args.due)
            sys.stdout.write("Added " + _display_task(task, color) + "\n")
        elif args.command == "list":
            if args.done:
                tasks = store.list_all(filter_done=True)
            elif args.open:
                tasks = store.list_all(filter_done=False)
            else:
                tasks = store.list_all()
            _print_tasks(tasks, color)
        elif args.command == "done":
            task = store.set_done(args.id, True)
            sys.stdout.write("Done: " + format_task(task) + "\n")
        elif args.command == "undo":
            task = store.set_done(args.id, False)
            sys.stdout.write("Undone: " + format_task(task) + "\n")
        elif args.command == "edit":
            due = args.due
            if args.no_due:
                due = ""
            task = store.update(
                args.id, title=args.title, priority=args.priority, due=due
            )
            sys.stdout.write("Edited: " + format_task(task) + "\n")
        elif args.command == "rm":
            task = store.delete(args.id)
            sys.stdout.write("Removed: " + format_task(task) + "\n")
        elif args.command == "clear":
            removed = store.clear_done()
            sys.stdout.write(f"Cleared {removed} completed task(s).\n")
        elif args.command == "interactive":
            from .interactive import run_interactive
            return run_interactive(store, color=color)
    except TodoError as exc:
        sys.stderr.write(f"error: {exc}\n")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
