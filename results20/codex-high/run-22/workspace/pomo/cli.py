"""Command-line interface for the pomodoro timer."""
from __future__ import annotations

import argparse
import shutil
import sys
import time

from .core import Phase, PomodoroTimer
from .stats import DEFAULT_PATH, load, report, save


def _parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="pomo",
        description="A dependency-free pomodoro timer for the terminal.",
    )
    parser.add_argument(
        "command",
        nargs="?",
        default="run",
        choices=["run", "report", "reset"],
        help="command to run (default: run)",
    )
    parser.add_argument("-t", "--task", default="", help="label for the current work session")
    parser.add_argument("-w", "--work", type=int, default=25, help="work length in minutes")
    parser.add_argument("-s", "--short-break", type=int, default=5, help="short break in minutes")
    parser.add_argument("-l", "--long-break", type=int, default=15, help="long break in minutes")
    parser.add_argument("-n", "--long-break-every", type=int, default=4, help="pomodoros before a long break")
    parser.add_argument("--stats-path", default=DEFAULT_PATH, help="path to the stats JSON file")
    return parser.parse_args(argv)


def _render(timer: PomodoroTimer, width: int) -> str:
    """Render the live timer view: label, remaining time, and progress bar."""
    total = max(timer.total_s, 1)
    pct = min(1.0, 1.0 - timer.remaining_s / total)
    filled = int(pct * width)
    bar = "#" * filled + "-" * (width - filled)
    mm, ss = divmod(timer.remaining_s, 60)
    task = timer._task or "Untitled task"
    return (
        f"[{timer.phase_name}] {task}\n"
        f"{mm:02d}:{ss:02d}  [{bar}] {pct * 100:3.0f}%"
    )


def run_timer(args: argparse.Namespace) -> int:
    timer = PomodoroTimer(
        work_s=args.work * 60,
        short_break_s=args.short_break * 60,
        long_break_s=args.long_break * 60,
        long_break_every=args.long_break_every,
    )
    timer.set_task(args.task)
    sessions = load(args.stats_path)

    cols = max(shutil.get_terminal_size((80, 24)).columns - 8, 10)
    try:
        while True:
            timer.tick()
            sys.stdout.write("\r" + _render(timer, cols) + " " * 4)
            sys.stdout.flush()
            time.sleep(0.2)
            if timer.remaining_s <= 0:
                timer.advance()
                if timer.phase is Phase.WORK:
                    print("\n" + ("=" * (cols + 8)))
                    print("Break finished. Starting a new work session.")
                else:
                    print("\n" + ("=" * (cols + 8)))
                    print(f"Nice work! {timer.completed_work} pomodoro(s) done. Take a break.")
    except KeyboardInterrupt:
        print("\nInterrupted. Saving completed sessions...")

    save(sessions + timer.sessions, args.stats_path)
    print(report(sessions + timer.sessions))
    return 0


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(argv if argv is not None else sys.argv[1:])
    if args.command == "report":
        print(report(load(args.stats_path)))
        return 0
    if args.command == "reset":
        # Resetting without confirmation would be unfriendly for a stats file.
        if "--yes" in (argv if argv is not None else sys.argv[1:]):
            save([], args.stats_path)
            print("Stats reset.")
            return 0
        print("Use 'pomo reset --yes' to confirm resetting stats.")
        return 1
    return run_timer(args)


if __name__ == "__main__":
    raise SystemExit(main())
