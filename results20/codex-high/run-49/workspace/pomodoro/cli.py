"""Command-line interface for the Pomodoro focus timer."""

from __future__ import annotations

import argparse
import sys
import time

from .core import (
    DEFAULT_FOCUS_MINUTES,
    DEFAULT_LONG_BREAK_MINUTES,
    DEFAULT_SESSIONS_PER_CYCLE,
    DEFAULT_SHORT_BREAK_MINUTES,
    Timer,
    format_time,
)


def _parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="pomodoro",
        description="A tiny Pomodoro focus timer for your terminal.",
    )
    parser.add_argument(
        "--focus",
        type=int,
        default=DEFAULT_FOCUS_MINUTES,
        metavar="MIN",
        help="focus session length in minutes (default: %(default)s)",
    )
    parser.add_argument(
        "--short-break",
        type=int,
        default=DEFAULT_SHORT_BREAK_MINUTES,
        metavar="MIN",
        help="short break length in minutes (default: %(default)s)",
    )
    parser.add_argument(
        "--long-break",
        type=int,
        default=DEFAULT_LONG_BREAK_MINUTES,
        metavar="MIN",
        help="long break length in minutes (default: %(default)s)",
    )
    parser.add_argument(
        "--cycle",
        type=int,
        default=DEFAULT_SESSIONS_PER_CYCLE,
        metavar="N",
        help="focus sessions before a long break (default: %(default)s)",
    )
    parser.add_argument(
        "--non-interactive",
        action="store_true",
        help="render single-line progress instead of a redrawn clock",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(argv)

    try:
        timer = Timer(
            focus_minutes=args.focus,
            short_break_minutes=args.short_break,
            long_break_minutes=args.long_break,
            sessions_per_cycle=args.cycle,
        )
    except ValueError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2

    label = timer.session_type.value
    try:
        while True:
            timer.tick(1)
            display = f"{timer.session_type.value:>11} | {format_time(timer.remaining)} | focus #{timer.focus_count} | done {timer.completed_sessions}"
            if args.non_interactive:
                print(display, flush=True)
            else:
                print(f"\r{display}", end="", flush=True)
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nstopped", file=sys.stderr)
        return 0


if __name__ == "__main__":
    raise SystemExit(main())
