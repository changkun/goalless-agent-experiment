"""Command-line interface for the todo tracker."""

from __future__ import annotations

import argparse
import os
from pathlib import Path

from todo.store import TaskStore


def default_data_path() -> Path:
    home = Path(os.environ.get("HOME", "/tmp"))
    return home / ".todo.json"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="todo", description="Track tasks from the command line.")
    parser.add_argument("--data", type=Path, default=None, help="Path to the JSON data file.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    add_parser = subparsers.add_parser("add", help="Add a new task.")
    add_parser.add_argument("text", help="Task description.")

    list_parser = subparsers.add_parser("list", help="List pending tasks.")
    list_parser.add_argument("--all", action="store_true", help="Include completed tasks.")

    done_parser = subparsers.add_parser("done", help="Mark a task as done.")
    done_parser.add_argument("id", type=int, help="Task ID.")

    remove_parser = subparsers.add_parser("remove", help="Remove a task.")
    remove_parser.add_argument("id", type=int, help="Task ID.")

    return parser


def print_task(task) -> None:
    status = "x" if task.done else " "
    print(f"[{status}] {task.id}: {task.text}")


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    store = TaskStore(args.data or default_data_path())

    if args.command == "add":
        task = store.add(args.text)
        print(f"Added task {task.id}.")
    elif args.command == "list":
        tasks = store.list(show_all=args.all)
        if not tasks:
            print("No tasks found.")
        for task in tasks:
            print_task(task)
    elif args.command == "done":
        task = store.done(args.id)
        if task is None:
            print(f"Task {args.id} not found.")
            return 1
        print(f"Marked task {task.id} as done.")
    elif args.command == "remove":
        if not store.remove(args.id):
            print(f"Task {args.id} not found.")
            return 1
        print(f"Removed task {args.id}.")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
