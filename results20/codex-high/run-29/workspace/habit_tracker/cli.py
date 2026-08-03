"""Command-line interface for the habit tracker."""
from __future__ import annotations

import argparse
import sys
from datetime import timedelta

from .core import HabitStore, today_iso


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="habit",
        description="A dependency-free CLI habit tracker.",
    )
    parser.add_argument("--data", default=None, help="Path to the JSON data file.")
    sub = parser.add_subparsers(dest="command", required=True)

    add = sub.add_parser("add", help="Create a new habit.")
    add.add_argument("name", help="Name of the habit.")

    rm = sub.add_parser("rm", help="Remove a habit.")
    rm.add_argument("name", help="Name of the habit.")

    done = sub.add_parser("done", help="Mark a habit complete for today (or a date).")
    done.add_argument("name", help="Name of the habit.")
    done.add_argument("--date", default=None, help="ISO date (YYYY-MM-DD) to mark.")

    undo = sub.add_parser("undo", help="Unmark a habit for today (or a date).")
    undo.add_argument("name", help="Name of the habit.")
    undo.add_argument("--date", default=None, help="ISO date (YYYY-MM-DD) to unmark.")

    ls = sub.add_parser("list", help="List all habits with their streaks.")
    ls.add_argument("--verbose", action="store_true", help="Show detailed stats.")

    return parser


def _resolve_path(args) -> str:
    return args.data or "~/.habit_tracker.json"


def _resolve_store(args) -> HabitStore:
    from pathlib import Path

    return HabitStore(str(Path(_resolve_path(args)).expanduser()))


def cmd_list(store: HabitStore, verbose: bool) -> int:
    names = store.names()
    if not names:
        print("No habits yet. Add one with: habit add <name>")
        return 0
    width = max(len(n) for n in names)
    for name in names:
        streak = store.current_streak(name)
        checked = " ✓" if store.completions(name) else ""
        print(f"{name.ljust(width)}  streak {streak}{checked}")
        if verbose:
            print(
                f"    total {store.total_completions(name)}  "
                f"longest {store.longest_streak(name)}"
            )
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    store = _resolve_store(args)

    if args.command == "add":
        if store.add(args.name):
            store.save()
            print(f"Added habit: {args.name}")
        else:
            print(f"Habit already exists: {args.name}", file=sys.stderr)
            return 1
    elif args.command == "rm":
        if store.remove(args.name):
            store.save()
            print(f"Removed habit: {args.name}")
        else:
            print(f"No such habit: {args.name}", file=sys.stderr)
            return 1
    elif args.command == "done":
        if store.check_off(args.name, args.date):
            store.save()
            when = args.date or today_iso()
            print(f"Marked '{args.name}' complete for {when}")
        else:
            print(f"No such habit: {args.name}", file=sys.stderr)
            return 1
    elif args.command == "undo":
        if store.uncheck(args.name, args.date):
            store.save()
            when = args.date or today_iso()
            print(f"Unmarked '{args.name}' for {when}")
        else:
            print(f"No such habit: {args.name}", file=sys.stderr)
            return 1
    elif args.command == "list":
        return cmd_list(store, args.verbose)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
