#!/usr/bin/env python3
"""td — a tiny, dependency-free task tracker.

Store tasks in a single JSON file, edit them from a terminal with a few
short subcommands. No external dependencies; designed to be readable and
hackable.

Example:
    $ python3 td.py add "write release notes"
    $ python3 td.py add "refactor parser" --tag backend
    $ python3 td.py list
    $ python3 td.py done 1
    $ python3 td.py rm 1
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
from dataclasses import dataclass, field
from typing import Optional

DEFAULT_STORE = os.path.join(os.path.expanduser("~"), ".td.json")


@dataclass
class Task:
    id: int
    text: str
    done: bool = False
    tags: list[str] = field(default_factory=list)
    created_at: float = 0.0
    completed_at: Optional[float] = None


# --- storage -------------------------------------------------------------

class Store:
    def __init__(self, path: str) -> None:
        self.path = path
        self.tasks: list[Task] = []
        self._next_id = 1

    def load(self) -> "Store":
        try:
            with open(self.path, encoding="utf-8") as fh:
                data = json.load(fh)
        except (FileNotFoundError, json.JSONDecodeError):
            data = {"next_id": 1, "tasks": []}
        self._next_id = int(data.get("next_id", 1))
        for item in data.get("tasks", []):
            self.tasks.append(Task(**item))
        return self

    def save(self) -> None:
        payload = {
            "next_id": self._next_id,
            "tasks": [task.__dict__ for task in self.tasks],
        }
        tmp = self.path + ".tmp"
        with open(tmp, "w", encoding="utf-8") as fh:
            json.dump(payload, fh, indent=2, ensure_ascii=False)
        os.replace(tmp, self.path)  # atomic on POSIX


# --- helpers -------------------------------------------------------------

def _find(store: Store, task_id: int) -> Task:
    for task in store.tasks:
        if task.id == task_id:
            return task
    raise KeyError(f"no task #{task_id}")


def _next_id(store: Store) -> int:
    nid = store._next_id
    store._next_id += 1
    return nid


def _ts() -> float:
    return time.time()


# --- commands ------------------------------------------------------------

def cmd_add(store: Store, text: str, tags: list[str], verbose: bool = False) -> int:
    task = Task(
        id=_next_id(store),
        text=text,
        tags=tags,
        created_at=_ts(),
    )
    store.tasks.append(task)
    store.save()
    if verbose:
        print(f"added #{task.id}: {task.text}")
    return 0


def cmd_done(store: Store, task_id: int) -> int:
    task = _find(store, task_id)
    task.done = True
    task.completed_at = _ts()
    store.save()
    print(f"done #{task.id}: {task.text}")
    return 0


def cmd_undone(store: Store, task_id: int) -> int:
    task = _find(store, task_id)
    task.done = False
    task.completed_at = None
    store.save()
    print(f"reopened #{task.id}: {task.text}")
    return 0


def cmd_rm(store: Store, task_id: int) -> int:
    task = _find(store, task_id)
    store.tasks.remove(task)
    store.save()
    print(f"removed #{task.id}: {task.text}")
    return 0


def cmd_list(store: Store, only_done: bool, only_open: bool, tag: Optional[str]) -> int:
    tasks = store.tasks
    if only_done:
        tasks = [t for t in tasks if t.done]
    elif only_open:
        tasks = [t for t in tasks if not t.done]
    if tag:
        tasks = [t for t in tasks if tag in t.tags]
    tasks.sort(key=lambda t: (t.done, t.created_at))

    if not tasks:
        print("(nothing to show)")
    for t in tasks:
        mark = "x" if t.done else " "
        tag_str = "  [" + ", ".join(t.tags) + "]" if t.tags else ""
        print(f"[{mark}] #{t.id} {t.text}{tag_str}")

    open_count = sum(1 for t in tasks if not t.done)
    done_count = len(tasks) - open_count
    print(f"\n{open_count} open, {done_count} done")
    return 0


# --- CLI -----------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="td", description=__doc__.strip().splitlines()[0])
    parser.add_argument("--store", default=DEFAULT_STORE, help="path to the JSON store")
    sub = parser.add_subparsers(dest="command", required=True)

    pa = sub.add_parser("add", help="add a task")
    pa.add_argument("text", help="task text")
    pa.add_argument("--tag", "-t", action="append", default=[], help="tag (repeatable)")
    pa.add_argument("--verbose", "-v", action="store_true")

    pl = sub.add_parser("list", help="list tasks")
    pl.add_argument("--done", action="store_true", help="only done tasks")
    pl.add_argument("--open", action="store_true", help="only open tasks")
    pl.add_argument("--tag", default=None)

    for name, help_ in (("done", "mark a task done"), ("undone", "reopen a task"), ("rm", "delete a task")):
        p = sub.add_parser(name, help=help_)
        p.add_argument("id", type=int, help="task id")

    return parser


def main(argv: Optional[list[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    store = Store(args.store).load()

    try:
        if args.command == "add":
            return cmd_add(store, args.text, args.tag, args.verbose)
        if args.command == "done":
            return cmd_done(store, args.id)
        if args.command == "undone":
            return cmd_undone(store, args.id)
        if args.command == "rm":
            return cmd_rm(store, args.id)
        if args.command == "list":
            return cmd_list(store, args.done, args.open, args.tag)
    except KeyError as exc:
        print(str(exc), file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
