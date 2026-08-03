#!/usr/bin/env python3
"""pomo — a tiny, dependency-free Pomodoro timer for the terminal.

Usage:
    pomo.py [duration]
    pomo.py [work] [short] [long]

Durations accept a unit suffix: 25m, 5s, 1h (default m).

Controls:
    p  pause / resume
    s  skip current session
    q  quit
"""

from __future__ import annotations

import argparse
import shutil
import sys
import time
from dataclasses import dataclass

DEFAULTS = {"work": 25 * 60, "short": 5 * 60, "long": 15 * 60}
LONG_BREAK_EVERY = 4
FRAME = 0.1  # seconds between progress-bar redraws


@dataclass
class Timer:
    total: int
    remaining: float = 0.0
    running: bool = True

    def __post_init__(self) -> None:
        self.remaining = float(self.total)

    def tick(self, dt: float) -> None:
        if self.running:
            self.remaining = max(0.0, self.remaining - dt)

    @property
    def done(self) -> bool:
        return self.remaining <= 0.0

    @property
    def fraction(self) -> float:
        return self.remaining / self.total if self.total else 0.0


def parse_duration(text: str) -> int:
    text = text.strip().lower()
    if not text:
        raise ValueError("empty duration")
    if text.isdigit():
        return int(text) * 60
    unit = text[-1]
    try:
        amount = float(text[:-1])
    except ValueError:
        raise ValueError(f"cannot parse duration: {text!r}") from None
    scale = {"s": 1, "m": 60, "h": 3600}.get(unit)
    if scale is None:
        raise ValueError(f"unknown unit {unit!r} in {text!r} (use s, m, or h)")
    return max(1, int(amount * scale))


def parse_args(argv: list[str]) -> argparse.Namespace:
    ap = argparse.ArgumentParser(
        prog="pomo",
        description="A tiny, dependency-free Pomodoro timer for the terminal.",
        epilog="Controls: p pause/resume, s skip, q quit. Durations accept s/m/h suffixes.",
    )
    ap.add_argument(
        "durations",
        nargs="*",
        metavar="DURATION",
        help="optional overrides: work, short, long (defaults: 25m 5m 15m)",
    )
    return ap.parse_args(argv)


def load_durations(argv: list[str]) -> dict[str, int]:
    parts = parse_args(argv).durations
    out = dict(DEFAULTS)
    if len(parts) > 3:
        raise ValueError("at most three durations: work, short, long")
    for key, raw in zip(("work", "short", "long"), parts):
        out[key] = parse_duration(raw)
    return out


def format_clock(seconds: float) -> str:
    seconds = max(0, int(round(seconds)))
    h, rem = divmod(seconds, 3600)
    m, s = divmod(rem, 60)
    if h:
        return f"{h}:{m:02d}:{s:02d}"
    return f"{m:02d}:{s:02d}"


def render_bar(fraction: float, width: int) -> str:
    filled = int(round(fraction * width))
    return "█" * filled + "░" * (width - filled)


def build_frame(timer: Timer, label: str, completed: int, width: int) -> list[str]:
    frac_done = 1.0 - timer.fraction
    bar = render_bar(frac_done, width)
    status = "running" if timer.running else "paused "
    lines = [
        f" {label}",
        f" {bar}",
        f" {format_clock(timer.remaining)} left   {status}   {completed} done",
        f" [p] pause  [s] skip  [q] quit",
    ]
    return lines


def clear_lines(n: int) -> None:
    sys.stdout.write(f"\033[{n}A\033[K")
    for _ in range(n - 1):
        sys.stdout.write("\033[B\033[K")
    sys.stdout.flush()


def play_bell() -> None:
    sys.stdout.write("\a")
    sys.stdout.flush()


def wait_for_key(timeout: float) -> str | None:
    """Read a single keypress without blocking longer than `timeout` seconds.

    Uses raw mode on POSIX; falls back to a plain blocking input() elsewhere.
    """
    try:
        import termios
        import tty

        fd = sys.stdin.fileno()
        if not sys.stdin.isatty():
            raise OSError("not a tty")
        old = termios.tcgetattr(fd)
        try:
            tty.setraw(fd)
            import select

            ready, _, _ = select.select([fd], [], [], timeout)
            if not ready:
                return None
            return sys.stdin.read(1)
        finally:
            termios.tcsetattr(fd, termios.TCSADRAIN, old)
    except (ImportError, OSError, AttributeError):
        try:
            return sys.stdin.readline()[:1] or None
        except KeyboardInterrupt:
            return None


def run(work: int, short: int, long: int) -> None:
    names = {work: "WORK", short: "SHORT BREAK", long: "LONG BREAK"}
    completed = 0
    timers = [
        Timer(work),
        Timer(short),
        Timer(long),
    ]

    print(" pomo — press p to pause, s to skip, q to quit\n")
    time.sleep(0.5)

    idx = 0
    try:
        while True:
            timer = timers[idx]
            label = names[timer.total]
            width = max(10, shutil.get_terminal_size((80, 24)).columns - 4)
            last = time.monotonic()

            while not timer.done:
                now = time.monotonic()
                timer.tick(now - last)
                last = now
                frame = build_frame(timer, label, completed, width)
                print("\n".join(frame))
                if timer.done:
                    break
                clear_lines(len(frame))
                key = wait_for_key(FRAME)
                if key == "p":
                    timer.running = not timer.running
                elif key == "s":
                    break
                elif key in ("q", "\x03"):
                    print("\n\n bye! 👋")
                    return

            play_bell()
            completed += 1
            print(f" {label} finished — {completed} sessions done!")

            if timer.total == work and completed % LONG_BREAK_EVERY == 0:
                idx = 2  # long break
            elif timer.total != work:
                idx = 0  # back to work
            else:
                idx = 1  # short break
            print()
            time.sleep(0.75)
    except KeyboardInterrupt:
        print("\n\n bye! 👋")


def main() -> int:
    try:
        durations = load_durations(sys.argv[1:])
    except (ValueError, SystemExit) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    run(**durations)
    return 0


if __name__ == "__main__":
    sys.exit(main())
