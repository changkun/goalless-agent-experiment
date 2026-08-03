"""Command-line interface for the habit tracker."""

from __future__ import annotations

import argparse
import sys
from datetime import date
from pathlib import Path

from . import __version__
from .store import Habit, Store


def _parse_date(value: str) -> date:
    return date.fromisoformat(value)


def _render(habit: Habit) -> str:
    return f"{habit.name}: {habit.streak()} day streak, {habit.total} total"


def cmd_add(args: argparse.Namespace, store: Store) -> None:
    try:
        store.add(args.name)
    except ValueError as exc:
        print(f"error: {exc}", file=sys.stderr)
        raise SystemExit(1)
    print(f"Added: {args.name}")


def cmd_done(args: argparse.Namespace, store: Store) -> None:
    try:
        habit = store.complete(args.name, args.date)
    except KeyError as exc:
        print(f"error: {exc}", file=sys.stderr)
        raise SystemExit(1)
    print(f"{_render(habit)}  \u2713")


def cmd_undo(args: argparse.Namespace, store: Store) -> None:
    try:
        habit = store.uncomplete(args.name, args.date)
    except KeyError as exc:
        print(f"error: {exc}", file=sys.stderr)
        raise SystemExit(1)
    print(f"Undid {args.name}. {_render(habit)}")


def cmd_remove(args: argparse.Namespace, store: Store) -> None:
    try:
        store.remove(args.name)
    except KeyError as exc:
        print(f"error: {exc}", file=sys.stderr)
        raise SystemExit(1)
    print(f"Removed: {args.name}")


def cmd_list(args: argparse.Namespace, store: Store) -> None:
    habits = store.list()
    if not habits:
        print("No habits yet. Add one with: habits add <name>")
        return
    order = {"done": lambda h: (0, -h.streak()), "name": lambda h: (1, h.name)}
    key = order.get(args.sort, order["done"])
    for habit in sorted(habits, key=key):
        marker = "*" if habit.is_done(date.today()) else " "
        print(f"[{marker}] {_render(habit)}")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="habits",
        description="A tiny habit tracker with streaks.",
    )
    parser.add_argument("--version", action="version", version=__version__)
    parser.add_argument(
        "--store",
        type=Path,
        default=None,
        help="Path to the data file (default: ~/.habits/habits.json).",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    p_add = sub.add_parser("add", help="Add a new habit.")
    p_add.add_argument("name")
    p_add.set_defaults(func=cmd_add)

    p_done = sub.add_parser("done", help="Mark a habit done for a day.")
    p_done.add_argument("name")
    p_done.add_argument("--date", type=_parse_date, default=None)
    p_done.set_defaults(func=cmd_done)

    p_undo = sub.add_parser("undo", help="Un-mark a habit for a day.")
    p_undo.add_argument("name")
    p_undo.add_argument("--date", type=_parse_date, default=None)
    p_undo.set_defaults(func=cmd_undo)

    p_rm = sub.add_parser("remove", help="Delete a habit.")
    p_rm.add_argument("name")
    p_rm.set_defaults(func=cmd_remove)

    p_list = sub.add_parser("list", help="Show all habits.")
    p_list.add_argument("--sort", choices=["done", "name"], default="done")
    p_list.set_defaults(func=cmd_list)

    return parser


def main(argv: list[str] | None = None) -> None:
    parser = build_parser()
    args = parser.parse_args(argv)
    store = Store(args.store)
    args.func(args, store)


if __name__ == "__main__":
    main()
