"""Command-line interface for the focus tracker."""

from __future__ import annotations

import argparse
import os
import sys
from datetime import datetime
from pathlib import Path

from focus.session import Session, Store, summarize, today, total_minutes


def default_store_path() -> Path:
    data_dir = Path(os.environ.get("XDG_DATA_HOME", Path.home() / ".local" / "share"))
    return data_dir / "focus" / "sessions.jsonl"


def parse_tags(tags: str | None) -> tuple[str, ...]:
    if not tags:
        return ()
    return tuple(t.strip().lower() for t in tags.split(",") if t.strip())


def cmd_log(store: Store, args: argparse.Namespace) -> int:
    session = Session(
        task=" ".join(args.task),
        started_at=datetime.now(),
        duration_minutes=args.minutes,
        tags=parse_tags(args.tags),
    )
    store.add(session)
    print(f"Logged {session.duration_minutes}m: {session.task}")
    return 0


def cmd_today(store: Store, _args: argparse.Namespace) -> int:
    sessions = [s for s in store.sessions() if today(s)]
    if not sessions:
        print("No sessions logged today yet.")
        return 0

    print(f"Today: {total_minutes(sessions)} minutes across {len(sessions)} session(s)")
    for tag, minutes in sorted(summarize(sessions).items()):
        print(f"  {tag}: {minutes}m")
    return 0


def cmd_history(store: Store, _args: argparse.Namespace) -> int:
    sessions = store.sessions()
    if not sessions:
        print("No sessions logged yet.")
        return 0

    for s in sessions:
        tags = ", ".join(s.tags) if s.tags else "untagged"
        print(f"{s.started_at:%Y-%m-%d %H:%M}  {s.duration_minutes:3d}m  [{tags}]  {s.task}")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="focus", description="Track focused work sessions.")
    parser.add_argument("--store", type=Path, default=default_store_path(), help="Path to session store")
    subparsers = parser.add_subparsers(dest="command", required=True)

    log = subparsers.add_parser("log", help="Log a completed session")
    log.add_argument("task", nargs="+", help="What you worked on")
    log.add_argument("--minutes", "-m", type=int, required=True, help="Duration in minutes")
    log.add_argument("--tags", "-t", help="Comma-separated tags")

    subparsers.add_parser("today", help="Show today's summary")
    subparsers.add_parser("history", help="Show all logged sessions")

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    store = Store(args.store)

    if args.command == "log":
        return cmd_log(store, args)
    if args.command == "today":
        return cmd_today(store, args)
    if args.command == "history":
        return cmd_history(store, args)

    parser.print_help()
    return 1


if __name__ == "__main__":
    sys.exit(main())
