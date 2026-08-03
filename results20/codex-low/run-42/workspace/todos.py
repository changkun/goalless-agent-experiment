#!/usr/bin/env python3
"""todos.py — a tiny, friendly task tracker that persists to JSON.

Usage:
  python3 todos.py add "write a poem" [--priority high]
  python3 todos.py list [--due today]
  python3 todos.py done <id>...
  python3 todos.py clear
  python3 todos.py stats
"""

import argparse
import json
import os
import sys
from datetime import date, datetime
from pathlib import Path

STORAGE_ENV = "TODOS_FILE"
DEFAULT_FILE = "~/.todos.json"


class Todo:
    def __init__(self, text, priority="medium", created=None, completed=False):
        self.text = text
        self.priority = priority
        self.created = created or date.today().isoformat()
        self.completed = completed

    def to_dict(self):
        return {
            "text": self.text,
            "priority": self.priority,
            "created": self.created,
            "completed": self.completed,
        }


def load(path):
    if not path.exists():
        return []
    with open(path, "r", encoding="utf-8") as fh:
        data = json.load(fh)
    return [Todo(**row) for row in data]


def save(path, todos):
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as fh:
        json.dump([t.to_dict() for t in todos], fh, indent=2, ensure_ascii=False)
        fh.write("\n")


PRIORITY_ICON = {"high": "🔥", "medium": "📌", "low": "🌱"}
DONE_ICON = "✅"


def describe(todo):
    status = DONE_ICON if todo.completed else PRIORITY_ICON.get(todo.priority, "⚪")
    return f"[{status}] {todo.text}"


def main(argv=None):
    parser = argparse.ArgumentParser(
        prog="todos", description="A tiny, friendly task tracker."
    )
    sub = parser.add_subparsers(dest="command", required=True)

    p_add = sub.add_parser("add", help="Add a task")
    p_add.add_argument("text", help="What needs doing?")
    p_add.add_argument("--priority", choices=["high", "medium", "low"], default="medium")
    p_add.add_argument("--due", help="Optional due date (YYYY-MM-DD)")

    sub.add_parser("list", help="Show tasks")
    sub.add_parser("clear", help="Clear all tasks")
    sub.add_parser("stats", help="Show completion stats")

    p_done = sub.add_parser("done", help="Mark tasks complete")
    p_done.add_argument("ids", nargs="+", type=int, help="Task ids (from list)")

    args = parser.parse_args(argv)

    path = Path(os.environ.get(STORAGE_ENV, DEFAULT_FILE)).expanduser()
    todos = load(path)

    if args.command == "add":
        if args.due:
            try:
                datetime.strptime(args.due, "%Y-%m-%d")
            except ValueError:
                parser.error(f"--due must be YYYY-MM-DD, got {args.due!r}")
        todos.append(Todo(args.text, args.priority))
        save(path, todos)
        print(f"Added task {len(todos)}: {describe(todos[-1])}")

    elif args.command == "list":
        if not todos:
            print("Nothing to do. Enjoy the calm. 🌤️")
            return 0
        for i, todo in enumerate(todos, 1):
            print(f"{i:>3}. {describe(todo)}")

    elif args.command == "done":
        missing = [i for i in args.ids if i < 1 or i > len(todos)]
        if missing:
            print(f"No such task id(s): {', '.join(map(str, missing))}", file=sys.stderr)
            return 1
        for i in args.ids:
            todos[i - 1].completed = True
        save(path, todos)
        print(f"Marked {len(args.ids)} task(s) done. Nice work! 🎉")

    elif args.command == "clear":
        save(path, [])
        print("Cleared all tasks.")

    elif args.command == "stats":
        total = len(todos)
        done = sum(1 for t in todos if t.completed)
        pct = int((done / total) * 100) if total else 0
        bar = "█" * (pct // 10) + "░" * (10 - pct // 10)
        print(f"{total} total, {done} done, {pct}% complete")
        print(f"  [{bar}]")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
