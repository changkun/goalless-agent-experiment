"""Command-line entry point for the journal.

Persists to a JSON file (default ``~/.journal.json``, override with the
``JOURNAL_FILE`` env var). Creates the file on first write.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import date
from pathlib import Path

from .core import Journal


def default_path() -> Path:
    return Path(os.environ.get("JOURNAL_FILE", Path.home() / ".journal.json"))


def load(path: Path) -> Journal:
    if path.exists():
        data = json.loads(path.read_text())
    else:
        data = {}
    return Journal(data)


def save(journal: Journal, path: Path) -> None:
    path.write_text(json.dumps(journal.data, indent=2, sort_keys=True) + "\n")


def _print_streaks(journal: Journal) -> None:
    streaks = journal.streaks()
    if not streaks:
        print("No habits yet. Add one with: journal habit add <name>")
        return
    width = max(len(n) for n in streaks)
    for name in journal.habit_names():
        s = streaks[name]
        flame = "🔥" if s >= 7 else ("✨" if s >= 1 else "·")
        print(f"{name:<{width}}  {s:>3}d  {flame}")


def _print_day(journal: Journal, d: date) -> None:
    print(f"== {d.isoformat()} ==")
    entries = journal.entries_for(d)
    if entries:
        for i, e in enumerate(entries, 1):
            print(f"  {i}. {e}")
    else:
        print("  (no entries)")
    day_habits = [
        name
        for name in journal.habit_names()
        if d.isoformat() in journal.data["habits"][name]["days"]
    ]
    if day_habits:
        print(f"  Habits: {', '.join(day_habits)}")


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="journal", description=__doc__)
    sub = p.add_subparsers(dest="cmd", required=True)

    sub.add_parser("today", help="show today's entries and streaks")

    d = sub.add_parser("add", help="append an entry to today")
    d.add_argument("text", nargs="+", help="entry text")

    h = sub.add_parser("habit", help="manage habits")
    hsub = h.add_subparsers(dest="sub", required=True)
    ha = hsub.add_parser("add", help="create a habit")
    ha.add_argument("name", nargs="+")
    hd = hsub.add_parser("done", help="mark a habit done for today")
    hd.add_argument("name", nargs="+")
    hl = hsub.add_parser("list", help="list habits with streaks")
    hrm = hsub.add_parser("remove", help="delete a habit")
    hrm.add_argument("name", nargs="+")

    p.add_argument(
        "--file",
        default=None,
        help="journal file path (default: $JOURNAL_FILE or ~/.journal.json)",
    )
    return p


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    path = Path(args.file) if args.file else default_path()
    journal = load(path)
    today = journal.today

    if args.cmd == "today":
        _print_day(journal, today)
        print()
        _print_streaks(journal)

    elif args.cmd == "add":
        journal.add_entry(" ".join(args.text))
        save(journal, path)
        print("Saved.")

    elif args.cmd == "habit":
        if args.sub == "add":
            journal.add_habit(" ".join(args.name))
            save(journal, path)
            print(f"Habit added: {' '.join(args.name)}")
        elif args.sub == "done":
            try:
                journal.done(" ".join(args.name))
            except KeyError as e:
                print(e, file=sys.stderr)
                return 1
            save(journal, path)
            print("Marked done.")
        elif args.sub == "list":
            _print_streaks(journal)
        elif args.sub == "remove":
            journal.untrack(" ".join(args.name))
            save(journal, path)
            print("Removed.")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
