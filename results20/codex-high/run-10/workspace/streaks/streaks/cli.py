"""Command-line interface for the streak tracker."""

import argparse
import sys
from datetime import date

from .streak import current_streak, longest_streak
from .store import Store


def main(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    parser = _build_parser()
    args = parser.parse_args(argv)

    store = Store(path=args.path or args.main_path).load()

    if args.command == "add":
        store.add_habit(args.name).save()
        print(f"Added habit: {args.name}")
    elif args.command == "check":
        store.check(args.name, args.date or date.today().isoformat()).save()
        print(f"Checked {args.name}.")
    elif args.command == "uncheck":
        day = args.date or date.today().isoformat()
        store.uncheck(args.name, day).save()
        print(f"Unchecked {args.name} for {day}.")
    elif args.command == "status":
        _print_status(args, store)
    elif args.command == "remove":
        if args.name in store.data:
            del store.data[args.name]
            store.save()
            print(f"Removed habit: {args.name}")
        else:
            print(f"No habit named: {args.name}", file=sys.stderr)
            return 1
    return 0


def _print_status(args, store):
    habits = store.habits()
    if args.name:
        habits = [h for h in habits if h == args.name]
        if not habits:
            print(f"No habit named: {args.name}", file=sys.stderr)
            sys.exit(1)
    if not habits:
        print("No habits yet. Add one with: streaks add <name>")
        return
    width = max(len(h) for h in habits)
    for habit in habits:
        current = current_streak(store.data[habit])
        longest = longest_streak(store.data[habit])
        total = len(store.data[habit])
        print(f"{habit:<{width}}  current={current:>3}  longest={longest:>3}  total={total:>3}")


def _build_parser():
    parser = argparse.ArgumentParser(prog="streaks", description="Track habit streaks locally.")
    common = argparse.ArgumentParser(add_help=False)
    common.add_argument("--path", help="Path to the JSON data file (default: ~/.streaks.json)")
    parser.add_argument("--path", dest="main_path", help=argparse.SUPPRESS, default=None)
    sub = parser.add_subparsers(dest="command", required=True)

    add = sub.add_parser("add", help="Create a new habit", parents=[common])
    add.add_argument("name")

    check = sub.add_parser("check", help="Check off a habit for a day", parents=[common])
    check.add_argument("name")
    check.add_argument("--date", help="ISO date to check (default: today)")

    uncheck = sub.add_parser("uncheck", help="Remove a check for a day", parents=[common])
    uncheck.add_argument("name")
    uncheck.add_argument("--date", help="ISO date to uncheck (default: today)")

    status = sub.add_parser("status", help="Show streak status", parents=[common])
    status.add_argument("name", nargs="?")

    remove = sub.add_parser("remove", help="Delete a habit", parents=[common])
    remove.add_argument("name")

    return parser


if __name__ == "__main__":
    raise SystemExit(main())
