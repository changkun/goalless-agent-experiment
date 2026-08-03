"""Command-line interface for focus."""

from __future__ import annotations

import argparse
import datetime as dt
import shutil
import sys
from typing import List, Optional, Sequence

from . import __version__
from .storage import STATUS_OPEN, Task, TaskStore
from .timer import DEFAULT_BREAK_MIN, DEFAULT_FOCUS_MIN, run_timer

GREEN = "\033[32m"
DIM = "\033[2m"
BOLD = "\033[1m"
RED = "\033[31m"
RESET = "\033[0m"


def _parse_tags(values: Optional[Sequence[str]]) -> List[str]:
    if not values:
        return []
    tags: List[str] = []
    for value in values:
        for part in value.split(","):
            part = part.strip()
            if part and part not in tags:
                tags.append(part)
    return tags


def _tag_str(task: Task) -> str:
    if not task.tags:
        return ""
    return " " + DIM + "[" + ", ".join(task.tags) + "]" + RESET


def _print_list(tasks: List[Task]) -> None:
    if not tasks:
        print("No tasks.")
        return
    width = max((len(str(t.id)) for t in tasks), default=1)
    for task in tasks:
        flagged = "★" if task.pomodoros else " "
        line = f"  {task.id:>{width}}  {flagged}  {task.title}{_tag_str(task)}"
        if task.pomodoros:
            line += f"  {DIM}({task.pomodoros}🍅){RESET}"
        color = RESET if task.status == STATUS_OPEN else DIM
        print(color + line + RESET)


def ordered_open(tasks: List[Task]) -> List[Task]:
    return sorted(
        (t for t in tasks if t.status == STATUS_OPEN),
        key=lambda t: (not t.pomodoros, t.created_at),
    )


def _cmd_add(store: TaskStore, args: argparse.Namespace) -> int:
    tags = _parse_tags(args.tag)
    task = store.add(args.title, tags)
    store.save()
    print(f"{GREEN}✓{RESET} Added task {task.id}: {task.title}")
    return 0


def _cmd_list(store: TaskStore, args: argparse.Namespace) -> int:
    all_tasks = store.tasks if args.all else ordered_open(store.tasks)
    _print_list(all_tasks)
    return 0


def _cmd_done(store: TaskStore, args: argparse.Namespace) -> int:
    if not store.close(args.id):
        print(f"{RED}✗{RESET} No open task with id {args.id}.")
        return 1
    store.save()
    print(f"{GREEN}✓{RESET} Completed task {args.id}.")
    return 0


def _cmd_reopen(store: TaskStore, args: argparse.Namespace) -> int:
    if not store.reopen(args.id):
        print(f"{RED}✗{RESET} No closed task with id {args.id}.")
        return 1
    store.save()
    print(f"{GREEN}✓{RESET} Reopened task {args.id}.")
    return 0


def _cmd_rm(store: TaskStore, args: argparse.Namespace) -> int:
    if not store.remove(args.id):
        print(f"{RED}✗{RESET} No task with id {args.id}.")
        return 1
    store.save()
    print(f"{GREEN}✓{RESET} Removed task {args.id}.")
    return 0


def _cmd_clear(store: TaskStore, args: argparse.Namespace) -> int:
    count = store.clear_closed()
    store.save()
    print(f"{GREEN}✓{RESET} Cleared {count} completed task(s).")
    return 0


def _pick_task(store: TaskStore, task_id: Optional[int]) -> Optional[Task]:
    if task_id is not None:
        return store.get(task_id)
    candidates = ordered_open(store.tasks)
    if not candidates:
        print("No open tasks. Add one with `focus add \"title\"`.")
        return None
    return candidates[0]


def _cmd_focus(store: TaskStore, args: argparse.Namespace) -> int:
    task = _pick_task(store, args.id)
    if task is None:
        return 1

    run_timer(
        minutes=args.minutes,
        label=task.title,
        on_done=lambda: store.add_pomodoro(task.id),
    )
    store.save()
    print(f"  That's {task.pomodoros} pomodoro(s) on task {task.id}.")
    return 0


def _cmd_start(store: TaskStore, args: argparse.Namespace) -> int:
    run_timer(minutes=args.minutes, label=args.label or "Session")
    return 0


def _cmd_stats(store: TaskStore, args: argparse.Namespace) -> int:
    open_tasks = store.open_tasks()
    closed = [t for t in store.tasks if t.status != STATUS_OPEN]
    total_pomodoros = sum(t.pomodoros for t in store.tasks)
    print(f"{BOLD}Summary{RESET}")
    print(f"  Open tasks:      {len(open_tasks)}")
    print(f"  Completed tasks: {len(closed)}")
    print(f"  Total pomodoros: {total_pomodoros}")
    if closed:
        latest = max(t.completed_at for t in closed if t.completed_at)
        when = dt.datetime.fromtimestamp(latest).strftime("%Y-%m-%d %H:%M")
        print(f"  Last completed:  {when}")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="focus",
        description="Track tasks and run Pomodoro sessions from your terminal.",
    )
    parser.add_argument("--version", action="version", version=f"focus {__version__}")

    sub = parser.add_subparsers(dest="command", metavar="COMMAND")

    p_add = sub.add_parser("add", help="add a new task")
    p_add.add_argument("title", help="task title")
    p_add.add_argument("-t", "--tag", action="append", help="comma-separated tag(s)")
    p_add.set_defaults(func=_cmd_add)

    p_list = sub.add_parser("list", aliases=["ls"], help="list tasks")
    p_list.add_argument("-a", "--all", action="store_true", help="include completed tasks")
    p_list.set_defaults(func=_cmd_list)

    p_done = sub.add_parser("done", help="mark a task completed")
    p_done.add_argument("id", type=int)
    p_done.set_defaults(func=_cmd_done)

    p_reopen = sub.add_parser("reopen", help="reopen a completed task")
    p_reopen.add_argument("id", type=int)
    p_reopen.set_defaults(func=_cmd_reopen)

    p_rm = sub.add_parser("rm", help="remove a task entirely")
    p_rm.add_argument("id", type=int)
    p_rm.set_defaults(func=_cmd_rm)

    p_clear = sub.add_parser("clear", help="remove all completed tasks")
    p_clear.set_defaults(func=_cmd_clear)

    p_focus = sub.add_parser("focus", help="run a pomodoro on a task")
    p_focus.add_argument("id", nargs="?", type=int, help="task id (defaults to oldest open)")
    p_focus.add_argument("-m", "--minutes", type=int, default=DEFAULT_FOCUS_MIN)
    p_focus.set_defaults(func=_cmd_focus)

    p_start = sub.add_parser("start", help="run a plain timer")
    p_start.add_argument("minutes", nargs="?", type=int, default=DEFAULT_FOCUS_MIN)
    p_start.add_argument("-l", "--label", help="timer label")
    p_start.set_defaults(func=_cmd_start)

    p_stats = sub.add_parser("stats", help="show summary statistics")
    p_stats.set_defaults(func=_cmd_stats)

    return parser


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if not getattr(args, "command", None):
        parser.print_help()
        return 0

    store = TaskStore()
    return args.func(store, args)


if __name__ == "__main__":
    sys.exit(main())
