#!/usr/bin/env python3
"""
focus — a terminal Pomodoro timer with no dependencies.

Runs focus / short-break / long-break phases with a live animated progress
bar and keyboard controls. Every completed focus block is logged to CSV so
you can review how you actually spent your time.

Keyboard:
    space  pause / resume
    s      skip to next phase
    r      reset current phase
    q      quit (current session is still logged)
"""

import argparse
import csv
import os
import sys
import time
from datetime import datetime
from pathlib import Path

try:
    # termios is available everywhere except Windows; keep it optional so the
    # timer still runs (minus arrow-key / key handling) on exotic platforms.
    import termios
    import tty
    import select
    _HAS_TTY = True
except ImportError:  # pragma: no cover - Windows fallback
    _HAS_TTY = False

DEFAULT_LOG = Path.home() / ".focus" / "log.csv"

# Terminal colour / effect codes.
RESET = "\x1b[0m"
BOLD = "\x1b[1m"
DIM = "\x1b[2m"
CLEAR_LINE = "\x1b[2K"
MOVE_UP = "\x1b[1A"

PHASE_COLORS = {
    "focus": "\x1b[36m",   # cyan
    "short": "\x1b[33m",   # yellow
    "long":  "\x1b[35m",   # magenta
}


class FocusTimer:
    """Tracks phase state and elapsed time for a single focus block."""

    def __init__(self, phase, duration):
        self.phase = phase          # 'focus' | 'short' | 'long'
        self.duration = duration    # total seconds for this phase
        self.elapsed = 0.0          # seconds spent (paused time excluded)
        self.paused = False

    def remaining(self):
        return max(0.0, self.duration - self.elapsed)

    def fraction(self):
        """0.0 -> 1.0 completion of the current phase."""
        return min(1.0, self.elapsed / self.duration if self.duration else 1.0)


def fmt(seconds):
    """Format seconds as M:SS."""
    seconds = int(seconds)
    return f"{seconds // 60}:{seconds % 60:02d}"


def fmt_label(name):
    return {"focus": "FOCUS", "short": "SHORT BREAK", "long": "LONG BREAK"}[name]


def _interactive():
    return _HAS_TTY and sys.stdin.isatty()


def key_available():
    """True if a keypress is queued on stdin."""
    if not _interactive():
        return False
    return bool(select.select([sys.stdin], [], [], 0)[0])


def read_key():
    """Read a single character without waiting for Enter."""
    if not _interactive():
        return None
    return sys.stdin.read(1)


class TTYContext:
    """Context manager that switches the terminal to raw (cbreak) mode."""

    def __enter__(self):
        if _HAS_TTY and sys.stdin.isatty():
            self.fd = sys.stdin.fileno()
            self.old = termios.tcgetattr(self.fd)
            tty.setcbreak(self.fd)
            self.active = True
        else:
            # Not an interactive terminal (e.g. piped input) — keep the timer
            # running as a plain countdown without raw-mode key handling.
            self.active = False
        return self

    def __exit__(self, *exc):
        if getattr(self, "active", False):
            termios.tcsetattr(self.fd, termios.TCSADRAIN, self.old)
        return False


def draw(timer, block_num, cycles_info, hint=True):
    """Redraw the single-line status area + progress bar in place."""
    bar_width = 40
    frac = timer.fraction()
    filled = int(bar_width * frac)
    bar = "█" * filled + "░" * (bar_width - filled)

    color = PHASE_COLORS[timer.phase]
    state = "▶ paused" if timer.paused else "▶ running"
    cycle = cycles_info or ""
    title = f"{BOLD}{color}{fmt_label(timer.phase)}{RESET}  {state}  block {block_num}{cycle}"

    line1 = (
        f"\r{CLEAR_LINE}{title}\n"
        f"{CLEAR_LINE}  {color}{bar}{RESET} "
        f"{color}{fmt(timer.elapsed)}{RESET} / {fmt(timer.duration)}   "
        f"({int(frac * 100)}%)"
    )
    sys.stdout.write(line1)

    # Second line: keep the progress line visible and show hints above it.
    if hint:
        hints = f"{DIM}[space] pause  [s] skip  [r] reset  [q] quit{RESET}"
        sys.stdout.write(f"\n{CLEAR_LINE}  {hints}")
    sys.stdout.flush()


def log_block(log_path, phase, duration, spent):
    """Append one focus block to the CSV log. Returns False on failure."""
    if phase != "focus":
        return True  # only focus blocks are logged
    try:
        log_path.parent.mkdir(parents=True, exist_ok=True)
        exists = log_path.exists()
        with open(log_path, "a", newline="") as fh:
            writer = csv.writer(fh)
            if not exists:
                writer.writerow(["datetime", "focus_seconds"])
            writer.writerow([datetime.now().isoformat(timespec="seconds"),
                             round(spent)])
        return True
    except OSError:
        return False


def parse_args(argv=None):
    ap = argparse.ArgumentParser(
        description="A terminal Pomodoro timer with session logging.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    ap.add_argument("--focus", type=int, default=25, metavar="MIN",
                    help="focus block length in minutes")
    ap.add_argument("--short", type=int, default=5, metavar="MIN",
                    help="short-break length in minutes")
    ap.add_argument("--long", type=int, default=15, metavar="MIN",
                    help="long-break length in minutes")
    ap.add_argument("--cycles", type=int, default=4, metavar="N",
                    help="insert a long break every Nth focus block")
    ap.add_argument("--log", type=str, default=str(DEFAULT_LOG),
                    help="path to the session CSV log")
    ap.add_argument("--no-hints", action="store_true",
                    help="hide the key hints line")
    return ap.parse_args(argv)


def main(argv=None):
    args = parse_args(argv)
    log_path = Path(args.log)

    durations = {
        "focus": args.focus * 60,
        "short": args.short * 60,
        "long": args.long * 60,
    }

    block = 0          # completed focus blocks so far
    phase = "focus"
    timer = FocusTimer(phase, durations[phase])
    last_tick = time.monotonic()

    print(f"{BOLD}focus{RESET} — press {DIM}[q]{RESET} to quit at any time.\n")

    with TTYContext():
        while True:
            now = time.monotonic()
            dt = now - last_tick
            last_tick = now

            if not timer.paused:
                timer.elapsed += dt

            if timer.remaining() <= 0:
                # Phase finished.
                if phase == "focus":
                    block += 1
                    logged = log_block(log_path, phase, timer.duration,
                                       timer.elapsed)
                    if not logged:
                        print(f"\n{CLEAR_LINE}{DIM}warning: could not write "
                              f"log to {log_path}{RESET}")
                    # Chime: a couple of bell characters, then move on.
                    sys.stdout.write("\a\a")
                    sys.stdout.flush()
                    # After a long enough focus block, give a long break.
                    if block % args.cycles == 0:
                        phase = "long"
                    else:
                        phase = "short"
                elif phase in ("short", "long"):
                    phase = "focus"
                timer = FocusTimer(phase, durations[phase])
                # A fresh line after the previous bar's hints.
                sys.stdout.write("\n")
                continue

            # Render.
            cycle = f"  ({block}/{args.cycles} → long)" if phase == "focus" else ""
            draw(timer, block, cycle, hint=not args.no_hints)

            if key_available():
                key = read_key()
                if key == " ":            # pause / resume
                    timer.paused = not timer.paused
                elif key == "s":          # skip phase
                    timer.elapsed = timer.duration
                elif key == "r":          # reset phase
                    timer.elapsed = 0.0
                elif key in ("q", "Q"):   # quit
                    if phase == "focus":
                        log_block(log_path, phase, timer.duration, timer.elapsed)
                    sys.stdout.write(f"\n{CLEAR_LINE}Bye. Focused on {BOLD}"
                                     f"{block}{RESET} blocks this run.\n")
                    return 0

            # Keep ~30ms per frame even while paused so polling stays snappy.
            time.sleep(0.03)


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except KeyboardInterrupt:
        print(f"\n{CLEAR_LINE}Interrupted.", file=sys.stderr)
        raise SystemExit(130)
