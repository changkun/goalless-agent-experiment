#!/usr/bin/env python3
"""A zero-dependency Pomodoro timer with configurable work/break lengths."""

import argparse
import signal
import sys
import time
from dataclasses import dataclass


@dataclass
class Config:
    work: int
    short_break: int
    long_break: int
    cycles: int


def parse_args(argv=None):
    parser = argparse.ArgumentParser(
        description="A simple Pomodoro timer that signals between sessions."
    )
    parser.add_argument("--work", type=int, default=25, help="work minutes (default: 25)")
    parser.add_argument(
        "--short-break", type=int, default=5, help="short break minutes (default: 5)"
    )
    parser.add_argument(
        "--long-break", type=int, default=15, help="long break minutes (default: 15)"
    )
    parser.add_argument(
        "--cycles", type=int, default=4, help="cycles before a long break (default: 4)"
    )
    parser.add_argument(
        "--interval", type=float, default=0.1, help="re-render interval in seconds"
    )
    args = parser.parse_args(argv)

    if args.work < 0 or args.short_break < 0 or args.long_break < 0 or args.cycles < 0:
        parser.error("durations and cycles must be non-negative")
    if args.interval <= 0:
        parser.error("--interval must be greater than 0")
    return args


def bell():
    """Ring the terminal bell so the user notices a session ended."""
    sys.stdout.write("\a")
    sys.stdout.flush()


def mmss(seconds):
    m, s = divmod(max(0, int(seconds)), 60)
    return f"{m:02d}:{s:02d}"


def render(label, total, remaining, width=40):
    frac = 1.0 if total == 0 else max(0.0, min(1.0, remaining / total))
    filled = int(frac * width)
    bar = "▓" * filled + "░" * (width - filled)
    sys.stdout.write(f"\r{label} {mmss(remaining)}/{mmss(total)} [ {bar} ]")
    sys.stdout.flush()


def run_timer(label, total, interval):
    """Count down `total` seconds, redrawing an in-place progress bar."""
    end = time.monotonic() + total
    while True:
        remaining = end - time.monotonic()
        if remaining <= 0:
            render(label, total, 0)
            break
        render(label, total, remaining)
        time.sleep(min(interval, remaining))


def main(argv=None):
    args = parse_args(argv)
    cfg = Config(
        work=args.work * 60,
        short_break=args.short_break * 60,
        long_break=args.long_break * 60,
        cycles=args.cycles,
    )

    def on_sigint(signum, frame):
        sys.stdout.write("\rInterrupted by Ctrl-C.\n")
        sys.stdout.flush()
        raise SystemExit(0)

    signal.signal(signal.SIGINT, on_sigint)

    session = 0
    try:
        while session < cfg.cycles:
            session += 1
            bell()
            run_timer(f"WORK {session}/{cfg.cycles}", cfg.work, args.interval)
            if session >= cfg.cycles:
                bell()
                run_timer("LONG BREAK", cfg.long_break, args.interval)
            else:
                bell()
                run_timer("SHORT BREAK", cfg.short_break, args.interval)
    finally:
        sys.stdout.write("\n")
        sys.stdout.flush()


if __name__ == "__main__":
    main()
