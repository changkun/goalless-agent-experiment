#!/usr/bin/env python3
"""tt — a tiny, dependency-free task tracker.

Tasks live in a single JSON file (default ~/.tt/tasks.json). Everything is
plain text: add, list, done, undo, delete. Colours are only used when stdout
is a TTY, so piping works cleanly.

Exit codes: 0 success, 1 user-facing error, 2 usage error.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import List, Optional

STORE_ENV = "TT_STORE"          # override the store path (used by tests)
VERSION = "1.0.0"


# --------------------------------------------------------------------------- #
# Model
# --------------------------------------------------------------------------- #
@dataclass
class Task:
    id: int
    text: str
    done: bool = False
    created_at: float = field(default_factory=time.time)
    done_at: Optional[float] = None


def _load(path: Path) -> List[Task]:
    if not path.exists():
        return []
    try:
        raw = json.loads(path.read_text())
    except (json.JSONDecodeError, OSError) as e:
        raise StoreError(f"could not read task store {path}: {e}")
    tasks = []
    for entry in raw:
        entry.setdefault("created_at", time.time())
        tasks.append(Task(**entry))
    return tasks


def _save(path: Path, tasks: List[Task]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(
        json.dumps([asdict(t) for t in tasks], indent=2) + "\n"
    )
    os.replace(tmp, path)


# --------------------------------------------------------------------------- #
# Terminal niceties
# --------------------------------------------------------------------------- #
class Palette:
    def __init__(self, enabled: bool):
        self.enabled = enabled

    def _wrap(self, code: str, s: str) -> str:
        return f"\033[{code}m{s}\033[0m" if self.enabled else s

    def green(self, s: str) -> str:
        return self._wrap("32", s)

    def red(self, s: str) -> str:
        return self._wrap("31", s)

    def dim(self, s: str) -> str:
        return self._wrap("2", s)

    def bold(self, s: str) -> str:
        return self._wrap("1", s)


def _now() -> str:
    return time.strftime("%Y-%m-%d %H:%M")


def _open() -> Path:
    if os.environ.get(STORE_ENV):
        return Path(os.environ[STORE_ENV])
    return Path.home() / ".tt" / "tasks.json"


# --------------------------------------------------------------------------- #
# Commands
# --------------------------------------------------------------------------- #
def _next_id(tasks: List[Task]) -> int:
    return (max((t.id for t in tasks), default=0)) + 1


def cmd_add(tasks: List[Task], args, store: Path) -> int:
    task = Task(id=_next_id(tasks), text=args.text)
    tasks.append(task)
    _save(store, tasks)
    return 0


def _find(tasks: List[Task], id_: int) -> Task:
    for t in tasks:
        if t.id == id_:
            return t
    raise StoreError(f"no task with id {id_}")


def cmd_done(tasks: List[Task], args, store: Path) -> int:
    task = _find(tasks, args.id)
    task.done = True
    task.done_at = time.time()
    _save(store, tasks)
    return 0


def cmd_undo(tasks: List[Task], args, store: Path) -> int:
    task = _find(tasks, args.id)
    task.done = False
    task.done_at = None
    _save(store, tasks)
    return 0


def cmd_delete(tasks: List[Task], args, store: Path) -> int:
    task = _find(tasks, args.id)
    tasks.remove(task)
    _save(store, tasks)
    return 0


def cmd_list(tasks: List[Task], args, store: Path) -> int:
    p = Palette(sys.stdout.isatty() and not args.plain)
    if not tasks:
        print(p.dim("no tasks — add one with: tt add \"buy milk\""))
        return 0

    open_tasks = [t for t in tasks if not t.done]
    done_tasks = [t for t in tasks if t.done]

    for t in open_tasks:
        print(f"  {p.bold(str(t.id)):>4}  {t.text}")
    if open_tasks and done_tasks:
        print()
    for t in done_tasks:
        print(f"  {p.dim(str(t.id)):>4}  {p.green('✓')} {p.dim(t.text)}")
    total = len(tasks)
    print(
        p.dim(
            f"\n{len(open_tasks)} open, {len(done_tasks)} done "
            f"({total} total)"
        )
    )
    return 0


def cmd_clear(tasks: List[Task], args, store: Path) -> int:
    """Remove all completed tasks."""
    kept = [t for t in tasks if not t.done]
    n = len(tasks) - len(kept)
    _save(store, kept)
    return 0


# --------------------------------------------------------------------------- #
# CLI
# --------------------------------------------------------------------------- #
class StoreError(Exception):
    """Raised for recoverable errors we want to print cleanly."""


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="tt",
        description="tt — a tiny, dependency-free task tracker.",
    )
    sub = parser.add_subparsers(dest="command", metavar="COMMAND")

    pa = sub.add_parser("add", help="add a new task")
    pa.add_argument("text", help="task text")
    pa.set_defaults(func=cmd_add)

    pl = sub.add_parser("list", aliases=["ls"], help="list tasks")
    pl.add_argument(
        "--plain", "-p", action="store_true",
        help="disable colour (auto-off when not a TTY)",
    )
    pl.set_defaults(func=cmd_list)

    pn = sub.add_parser("done", help="mark a task done")
    pn.add_argument("id", type=int)
    pn.set_defaults(func=cmd_done)

    pu = sub.add_parser("undo", help="reopen a finished task")
    pu.add_argument("id", type=int)
    pu.set_defaults(func=cmd_undo)

    pd = sub.add_parser("delete", aliases=["rm"], help="delete a task")
    pd.add_argument("id", type=int)
    pd.set_defaults(func=cmd_delete)

    pc = sub.add_parser("clear", help="remove all completed tasks")
    pc.set_defaults(func=cmd_clear)

    sub.add_parser("version", help="print version")

    return parser


def main(argv: Optional[List[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.command == "version":
        print(f"tt {VERSION}")
        return 0
    if args.command is None:
        parser.print_help()
        return 2

    store = _open()
    try:
        tasks = _load(store)
    except StoreError as e:
        print(f"tt: {e}", file=sys.stderr)
        return 1

    try:
        return args.func(tasks, args, store)
    except StoreError as e:
        print(f"tt: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
