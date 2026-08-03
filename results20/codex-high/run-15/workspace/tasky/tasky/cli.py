"""Command-line interface for tasky."""

from __future__ import annotations

import argparse
import sys
import time

from tasky import __version__
from tasky.tasks import TaskStore


def _fmt_time(ts: float) -> str:
    return time.strftime("%Y-%m-%d %H:%M", time.localtime(ts))


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="tasky",
        description="A tiny, zero-dependency command-line task tracker.",
    )
    parser.add_argument("--file", default="tasks.json", help="path to task store")
    parser.add_argument("--version", action="version", version=f"tasky {__version__}")
    sub = parser.add_subparsers(dest="command")

    add = sub.add_parser("add", help="add a new task")
    add.add_argument("title", help="task title")

    sub.add_parser("list", help="list all tasks")

    done = sub.add_parser("done", help="mark a task complete")
    done.add_argument("id", help="task id")

    undo = sub.add_parser("undo", help="mark a task incomplete")
    undo.add_argument("id", help="task id")

    rm = sub.add_parser("rm", help="delete a task")
    rm.add_argument("id", help="task id")

    sub.add_parser("clear", help="remove all tasks")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    store = TaskStore(args.file)

    if not args.command:
        parser.print_help()
        return 0

    if args.command == "add":
        task = store.add(args.title)
        print(f"added [{task.id}] {task.title}")
        return 0

    if args.command == "list":
        tasks = store.all()
        if not tasks:
            print("no tasks")
            return 0
        for task in tasks:
            box = "[x]" if task.done else "[ ]"
            print(f"{box} {task.id}  {task.title}  ({_fmt_time(task.created_at)})")
        return 0

    if args.command in ("done", "undo"):
        task = store.set_done(args.id, done=(args.command == "done"))
        if task is None:
            print(f"no task with id {args.id}", file=sys.stderr)
            return 1
        state = "done" if task.done else "not done"
        print(f"marked [{task.id}] {state}: {task.title}")
        return 0

    if args.command == "rm":
        if not store.remove(args.id):
            print(f"no task with id {args.id}", file=sys.stderr)
            return 1
        print(f"removed {args.id}")
        return 0

    if args.command == "clear":
        store.clear()
        print("cleared all tasks")
        return 0

    return 0
