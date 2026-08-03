"""Command-line interface for the habit tracker."""

from __future__ import annotations

import argparse
from datetime import date
from pathlib import Path
from typing import NoReturn

from habits.tracker import DEFAULT_STORE, Tracker


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="habits",
        description="Track habits and streaks from the command line.",
    )
    parser.add_argument(
        "--store",
        default=str(DEFAULT_STORE),
        help=f"path to the JSON store (default: {DEFAULT_STORE})",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    add = sub.add_parser("add", help="create a new habit")
    add.add_argument("name")
    add.add_argument(
        "-d", "--date", metavar="ISO", action="append", default=[],
        help="initial check-in date (ISO format); repeatable",
    )

    rm = sub.add_parser("remove", help="delete a habit")
    rm.add_argument("name")

    check = sub.add_parser("check", help="check in on a habit")
    check.add_argument("name")
    check.add_argument("date", nargs="?", default=None, help="ISO date (default: today)")

    uncheck = sub.add_parser("uncheck", help="uncheck a habit")
    uncheck.add_argument("name")
    uncheck.add_argument("date", nargs="?", default=None, help="ISO date (default: today)")

    sub.add_parser("list", help="list habits with streaks")

    return parser


def _require(parser: argparse.ArgumentParser, tracker: Tracker, name: str) -> None:
    if tracker.get(name) is None:
        parser.error(f"no habit named {name!r} — use 'add' first")


def _parse_day(parser: argparse.ArgumentParser, raw: str | None) -> date | None:
    if raw is None:
        return None
    try:
        return date.fromisoformat(raw)
    except ValueError:
        parser.error(f"invalid date {raw!r} (expected ISO, e.g. 2026-08-03)")


def main(argv: list[str] | None = None) -> None:
    parser = build_parser()
    args = parser.parse_args(argv)
    tracker = Tracker(Path(args.store))

    if args.command == "add":
        tracker.add(args.name, args.date)
        print(f"added habit: {args.name}")
    elif args.command == "remove":
        if tracker.remove(args.name):
            print(f"removed habit: {args.name}")
        else:
            parser.error(f"no habit named {args.name!r} — use 'add' first")
    elif args.command == "check":
        _require(parser, tracker, args.name)
        tracker.check_in(args.name, _parse_day(parser, args.date))
        print(f"checked {args.name}")
    elif args.command == "uncheck":
        _require(parser, tracker, args.name)
        tracker.uncheck(args.name, _parse_day(parser, args.date))
        print(f"unchecked {args.name}")
    elif args.command == "list":
        if not tracker.names():
            print("no habits yet — run 'habits add <name>'")
            return
        for name in tracker.names():
            habit = tracker.get(name)
            assert habit is not None
            print(f"{name}: streak={habit.streak()} total={habit.total_days()}")


def cli() -> NoReturn:
    main()
    raise SystemExit(0)


if __name__ == "__main__":
    main()
