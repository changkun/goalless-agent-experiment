"""Command-line interface for the focus timer."""

from __future__ import annotations

import argparse
import shutil
import sys
import time
from datetime import timedelta

from .core import Cycle, frame_at, PHASE_FOCUS

BAR_WIDTH = 20
BLOCK_LINES = 4


def _bar(percent: float, width: int) -> str:
    filled = max(0, min(width, int(round(percent * width))))
    return "█" * filled + "░" * (width - filled)


def _format_seconds(seconds: int) -> str:
    return str(timedelta(seconds=seconds)).lstrip("0") or "0"


def _render(frame, width: int) -> str:
    color = "\033[38;5;39m" if frame.is_focus else "\033[38;5;48m"
    reset = "\033[0m"
    bold = "\033[1m"
    break_seconds = frame.cycle_seconds - frame.phase_seconds
    phase_display = frame.phase_seconds if frame.is_focus else break_seconds
    return "\n".join(
        [
            f"  {bold}{color}{frame.label}{reset}   {_format_seconds(frame.remaining_seconds)}",
            f"  {_bar(frame.percent, width)}  {frame.percent * 100:3.0f}%",
            f"  completed focus sessions: {frame.completed_focus_sessions}",
            f"  focus {_format_seconds(frame.phase_seconds)} / break {_format_seconds(break_seconds)}"
            f"   (now in {phase_display}s phase)",
        ]
    )


def _move_up(lines: int) -> None:
    if lines:
        sys.stdout.write(f"\033[{lines}A\r")


def run(cycle: Cycle, duration_seconds: int | None) -> None:
    if duration_seconds is None:
        duration_seconds = cycle.cycle_seconds

    width = min(shutil.get_terminal_size((80, 24)).columns - 2, BAR_WIDTH)

    started = time.monotonic()
    last_key = None
    try:
        while True:
            elapsed = int(time.monotonic() - started)
            if elapsed >= duration_seconds:
                break
            frame = frame_at(elapsed, cycle)
            key = (frame.remaining_seconds, frame.phase)
            if key != last_key:
                if last_key is not None:
                    _move_up(BLOCK_LINES)
                print(_render(frame, width) + "\n")
                last_key = key
            time.sleep(0.1)
    except KeyboardInterrupt:
        print()
    finally:
        print()


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="focus",
        description="A tiny Pomodoro-style focus timer in your terminal.",
    )
    parser.add_argument(
        "--focus", type=float, default=25.0, help="focus length in minutes (default: 25)"
    )
    parser.add_argument(
        "--break", dest="break_", type=float, default=5.0, help="break length in minutes (default: 5)"
    )
    parser.add_argument(
        "--minutes", type=float, help="total duration in minutes (default: one full cycle)"
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    cycle = Cycle.from_minutes(args.focus, args.break_)
    duration = None if args.minutes is None else round(args.minutes * 60)
    run(cycle, duration)
    return 0


if __name__ == "__main__":
    sys.exit(main())
