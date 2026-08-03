#!/usr/bin/env python3
"""A tiny, zero-dependency terminal task tracker with a focus timer."""

from __future__ import annotations

import argparse
import json
import sys
import time
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import List, Optional


# ---------------------------------------------------------------------------
# Colour helpers
# ---------------------------------------------------------------------------

class C:
    """Tiny ANSI colour helper (auto-disables when not a TTY)."""

    RESET = "\033[0m"
    RED = "\033[31m"
    GREEN = "\033[32m"
    YELLOW = "\033[33m"
    BLUE = "\033[34m"
    MAGENTA = "\033[35m"
    CYAN = "\033[36m"
    BOLD = "\033[1m"
    DIM = "\033[2m"

    @classmethod
    def on(cls) -> bool:
        return sys.stdout.isatty()


def paint(text: str, *codes: str) -> str:
    if not C.on():
        return text
    prefix = "".join(getattr(C, code) for code in codes)
    return f"{prefix}{text}{C.RESET}"


# ---------------------------------------------------------------------------
# Data model
# ---------------------------------------------------------------------------

PRIORITIES = {"low", "med", "high"}
PRIORITY_ICON = {"low": "L", "med": "M", "high": "H"}
PRIORITY_COLOUR = {"low": "GREEN", "med": "YELLOW", "high": "RED"}


@dataclass
class Task:
    id: int
    description: str
    priority: str = "med"
    created: str = field(default_factory=lambda: datetime.now().isoformat(timespec="seconds"))
    done: bool = False
    completed_at: Optional[str] = None
    pomodoros: int = 0


class Store:
    """Load/save tasks to a JSON file under the user's home directory."""

    def __init__(self, path: Optional[Path] = None) -> None:
        self.path = path or Path.home() / ".todotimer" / "tasks.json"

    def load(self) -> List[Task]:
        if not self.path.exists():
            return []
        try:
            data = json.loads(self.path.read_text())
        except (json.JSONDecodeError, OSError):
            return []
        tasks = []
        for raw in data:
            tasks.append(
                Task(
                    id=raw.get("id", 0),
                    description=raw.get("description", ""),
                    priority=raw.get("priority", "med"),
                    created=raw.get("created", ""),
                    done=raw.get("done", False),
                    completed_at=raw.get("completed_at"),
                    pomodoros=raw.get("pomodoros", 0),
                )
            )
        return tasks

    def save(self, tasks: List[Task]) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        payload = [
            {
                "id": t.id,
                "description": t.description,
                "priority": t.priority,
                "created": t.created,
                "done": t.done,
                "completed_at": t.completed_at,
                "pomodoros": t.pomodoros,
            }
            for t in tasks
        ]
        self.path.write_text(json.dumps(payload, indent=2) + "\n")


# ---------------------------------------------------------------------------
# Core operations
# ---------------------------------------------------------------------------

def _next_id(tasks: List[Task]) -> int:
    return max((t.id for t in tasks), default=0) + 1


def add_task(store: Store, description: str, priority: str = "med") -> Task:
    tasks = store.load()
    task = Task(id=_next_id(tasks), description=description, priority=priority)
    tasks.append(task)
    store.save(tasks)
    return task


def _find_task(tasks: List[Task], task_id: int) -> Task:
    for t in tasks:
        if t.id == task_id:
            return t
    raise KeyError(f"no task with id {task_id}")


def mark_done(store: Store, task_id: int) -> Task:
    tasks = store.load()
    task = _find_task(tasks, task_id)
    task.done = True
    task.completed_at = datetime.now().isoformat(timespec="seconds")
    store.save(tasks)
    return task


def remove_task(store: Store, task_id: int) -> Task:
    tasks = store.load()
    task = _find_task(tasks, task_id)
    tasks = [t for t in tasks if t.id != task_id]
    store.save(tasks)
    return task


def list_tasks(store: Store, show_done: bool = True) -> List[Task]:
    tasks = store.load()
    tasks.sort(key=lambda t: (t.done, t.priority != "high", t.priority != "med"))
    if not show_done:
        tasks = [t for t in tasks if not t.done]
    return tasks


def record_pomodoro(store: Store, task_id: int) -> Task:
    tasks = store.load()
    task = _find_task(tasks, task_id)
    task.pomodoros += 1
    store.save(tasks)
    return task


# ---------------------------------------------------------------------------
# CLI rendering
# ---------------------------------------------------------------------------

def format_tasks(tasks: List[Task]) -> str:
    lines = []
    for t in tasks:
        box = "[x]" if t.done else "[ ]"
        priority_col = PRIORITY_COLOUR[t.priority]
        icon = paint(PRIORITY_ICON[t.priority], priority_col)
        desc = paint(t.description, "DIM") if t.done else t.description
        pomo = paint(f"| {t.pomodoros}p", "CYAN")
        lines.append(f"  {box} #{t.id:<3} {icon} {desc} {pomo}")
    return "\n".join(lines)


def render_list(store: Store, show_done: bool) -> int:
    tasks = list_tasks(store, show_done)
    if not tasks:
        print(paint('No tasks. Add one with: todo add "buy milk"', "DIM"))
        return 0
    header = paint("TASKS", "BOLD", "CYAN")
    print(header)
    print(format_tasks(tasks))
    return 0


def run_focus(store: Store, task_id: int, minutes: float) -> int:
    try:
        task = _find_task(store.load(), task_id)
    except KeyError as exc:
        print(paint(str(exc), "RED"))
        return 1

    if task.done:
        print(paint(f"'{task.description}' is already done. Pick something new!", "YELLOW"))
        return 1

    total = max(1, int(minutes * 60))
    label = f"[#{task.id}] {task.description}"
    try:
        for remaining in range(total, -1, -1):
            mins, secs = divmod(remaining, 60)
            bar_len = 24
            percent = (total - remaining) / total
            filled = int(percent * bar_len)
            bar = "=" * filled + "-" * (bar_len - filled)
            line = f"\r{paint(label, 'BOLD')}  {paint(bar, 'GREEN')}  {paint(f'{mins:02d}:{secs:02d}', 'CYAN')} "
            sys.stdout.write(line)
            sys.stdout.flush()
            time.sleep(1)
    except KeyboardInterrupt:
        sys.stdout.write("\n")
        print(paint("Focus session interrupted. Nothing counted.", "YELLOW"))
        return 1

    sys.stdout.write("\n")
    task = record_pomodoro(store, task_id)
    print(paint(f"Focus complete! '{task.description}' now has {task.pomodoros} pomodoro(s).", "GREEN"))
    return 0


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="todo",
        description="A tiny terminal task tracker with a focus timer.",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    add = sub.add_parser("add", help="add a new task")
    add.add_argument("description")
    add.add_argument("--priority", choices=sorted(PRIORITIES), default="med")

    list_p = sub.add_parser("list", help="list all tasks")
    list_p.add_argument("--incomplete", action="store_true", help="only show open tasks")

    done = sub.add_parser("done", help="mark a task done")
    done.add_argument("task_id", type=int)

    rm = sub.add_parser("rm", help="remove a task")
    rm.add_argument("task_id", type=int)

    focus = sub.add_parser("focus", help="run a pomodoro focus timer for a task")
    focus.add_argument("task_id", type=int)
    focus.add_argument("--minutes", type=float, default=25.0)

    return parser


def main(argv: Optional[List[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    store = Store()

    if args.command == "add":
        task = add_task(store, args.description, args.priority)
        print(f"Added #{task.id}: {task.description}")
        return 0

    if args.command == "list":
        return render_list(store, show_done=not args.incomplete)

    if args.command == "done":
        try:
            task = mark_done(store, args.task_id)
        except KeyError as exc:
            print(paint(str(exc), "RED"))
            return 1
        print(paint(f"Completed #{task.id}: {task.description}", "GREEN"))
        return 0

    if args.command == "rm":
        try:
            task = remove_task(store, args.task_id)
        except KeyError as exc:
            print(paint(str(exc), "RED"))
            return 1
        print(paint(f"Removed #{task.id}: {task.description}", "YELLOW"))
        return 0

    if args.command == "focus":
        return run_focus(store, args.task_id, args.minutes)

    print(paint("Unknown command", "RED"))
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
