#!/usr/bin/env python3
"""
focus_timer.py — a zero-dependency terminal focus timer.

Default 25-minute work sessions with 5-minute breaks, tracked in a JSON
history file (~/.focus_timer/history.json) so you can review how your time
actually went.

Usage:
    python3 focus_timer.py              # 25min work / 5min break, then repeat
    python3 focus_timer.py 45 10        # 45min work / 10min break
    python3 focus_timer.py --stats      # show past sessions
    python3 focus_timer.py --list       # list today's sessions
    python3 focus_timer.py --reset      # clear history

Keys while a timer runs:
    space / p   pause or resume
    s           skip to the next phase
    r           restart the current phase
    q / ctrl-c  quit (current session is discarded)
"""

from __future__ import annotations

import argparse
import json
import os
import platform
import shutil
import signal
import sys
import time
from dataclasses import dataclass, asdict
from datetime import date, datetime, timedelta
from pathlib import Path

VERSION = "1.0.0"

# --------------------------------------------------------------------------
# Configuration & storage
# --------------------------------------------------------------------------

APP_NAME = "focus_timer"
DATA_DIR = Path(os.environ.get("XDG_DATA_HOME", Path.home() / ".local" / "share"))
HISTORY_FILE = DATA_DIR / APP_NAME / "history.json"

# ANSI colors / styles. Unsupported terminals degrade gracefully via
# _supports_color().
COLORS = {
    "reset": "\033[0m",
    "bold": "\033[1m",
    "dim": "\033[2m",
    "red": "\033[91m",
    "green": "\033[92m",
    "yellow": "\033[93m",
    "blue": "\033[94m",
    "magenta": "\033[95m",
    "cyan": "\033[96m",
}

PHASE_WORK = "work"
PHASE_BREAK = "break"
PHASES = (PHASE_WORK, PHASE_BREAK)

PHASE_LABEL = {
    PHASE_WORK: "FOCUS",
    PHASE_BREAK: "BREAK",
}

PHASE_COLOR = {
    PHASE_WORK: COLORS["cyan"],
    PHASE_BREAK: COLORS["green"],
}

CLEAR_LINE = "\033[K"
HIDE_CURSOR = "\033[?25l"
SHOW_CURSOR = "\033[?25h"
MOVE_UP = "\033[1A"

_SIGINT_SEEN = False


@dataclass
class Session:
    """One completed focus interval."""

    start: str      # ISO datetime when the phase started
    end: str        # ISO datetime when the phase ended
    minutes: int    # planned length in minutes
    planned: str    # 'work' or 'break'
    type: str = "focus"

    def __post_init__(self) -> None:
        # Backwards tolerance: sessions recorded before 'type' existed are
        # all focus work sessions.
        if not self.type:
            self.type = "focus"


# --------------------------------------------------------------------------
# Small terminal helpers
# --------------------------------------------------------------------------


def _supports_color() -> bool:
    if os.environ.get("NO_COLOR"):
        return False
    if os.environ.get("TERM") == "dumb":
        return False
    return True


def style(text: str, *keys: str) -> str:
    if not (_supports_color() and sys.stdout.isatty()):
        return text
    codes = "".join(COLORS[k] for k in keys if k in COLORS)
    return f"{codes}{text}{COLORS['reset']}"


def terminal_size() -> tuple[int, int]:
    """Return (columns, rows) with a safe fallback."""
    try:
        size = shutil.get_terminal_size((80, 24))
        return size.columns, size.lines
    except Exception:
        return 80, 24


def _on_sigint(signum, frame) -> None:  # noqa: ARG001
    global _SIGINT_SEEN
    _SIGINT_SEEN = True


class _RawTTY:
    """Context manager that puts the terminal into raw/cbreak mode and
    restores it afterwards, no matter how the block exits.

    In cbreak mode on POSIX the terminal echoes and blocks by default, so we
    also flip on O_NONBLOCK on stdin to make reads non-blocking for the
    key-polling loop.
    """

    def __init__(self) -> None:
        self._fd = None
        self._old_attrs = None
        self._old_flags = None

    def __enter__(self):
        if platform.system() == "Windows":
            try:
                import msvcrt  # type: ignore
            except ImportError:
                return self
            self._msvcrt = msvcrt
            return self
        self._fd = sys.stdin.fileno()
        import termios

        self._old_attrs = termios.tcgetattr(self._fd)
        new = termios.tcgetattr(self._fd)
        new[3] &= ~(termios.ICANON | termios.ECHO)
        termios.tcsetattr(self._fd, termios.TCSADRAIN, new)
        import fcntl

        self._old_flags = fcntl.fcntl(self._fd, fcntl.F_GETFL)
        fcntl.fcntl(self._fd, fcntl.F_SETFL, self._old_flags | os.O_NONBLOCK)
        return self

    def __exit__(self, *exc) -> None:
        if self._fd is not None and self._old_attrs is not None:
            import termios

            termios.tcsetattr(self._fd, termios.TCSADRAIN, self._old_attrs)
        if self._fd is not None and self._old_flags is not None:
            import fcntl

            fcntl.fcntl(self._fd, fcntl.F_SETFL, self._old_flags)

    def get_key(self) -> str | None:
        """Return one keypress, or None if nothing was pressed.

        Space and Enter both return ' ' so the same code paths handle pause.
        """
        if platform.system() == "Windows":
            try:
                if self._msvcrt.kbhit():
                    ch = self._msvcrt.getwch()
                    if ch in ("\r", "\n"):
                        return " "
                    return ch
            except Exception:
                pass
            return None
        try:
            import select

            if not select.select([sys.stdin], [], [], 0)[0]:
                return None
            ch = os.read(self._fd, 1)
            if not ch:
                return None
            ch = ch.decode("utf-8", errors="replace")
            if ch in ("\r", "\n"):
                return " "
            return ch
        except (BlockingIOError, OSError):
            return None


def _bell() -> None:
    try:
        sys.stdout.write("\a")
        sys.stdout.flush()
    except Exception:
        pass


# --------------------------------------------------------------------------
# History persistence
# --------------------------------------------------------------------------


def load_history() -> list[Session]:
    if not HISTORY_FILE.exists():
        return []
    try:
        raw = json.loads(HISTORY_FILE.read_text(encoding="utf-8"))
        return [Session(**s) for s in raw]
    except (json.JSONDecodeError, TypeError, KeyError, ValueError):
        # A corrupt file is worse than no file; don't silently lose the
        # ability to record new sessions.
        return []


def save_history(sessions: list[Session]) -> None:
    HISTORY_FILE.parent.mkdir(parents=True, exist_ok=True)
    payload = json.dumps([asdict(s) for s in sessions], indent=2)
    # Atomic-ish write: write to temp then rename so a crash mid-write can't
    # corrupt the history.
    tmp = HISTORY_FILE.with_suffix(".tmp")
    tmp.write_text(payload + "\n", encoding="utf-8")
    tmp.replace(HISTORY_FILE)


def record(session: Session) -> list[Session]:
    history = load_history()
    history.append(session)
    save_history(history)
    return history


# --------------------------------------------------------------------------
# Stats & reporting
# --------------------------------------------------------------------------


def _parse_iso(value: str) -> datetime:
    return datetime.fromisoformat(value)


def _minutes_worked(sessions: list[Session]) -> int:
    return sum(
        round((_parse_iso(s.end) - _parse_iso(s.start)).total_seconds() / 60)
        for s in sessions
    )


def stats(sessions: list[Session]) -> str:
    if not sessions:
        return style("No sessions recorded yet. Run a timer to start.", COLORS["dim"])

    today = date.today()
    todays = [s for s in sessions if _parse_iso(s.start).date() == today]
    week_ago = datetime.combine(today - timedelta(days=7), datetime.min.time())
    last7 = [s for s in sessions if _parse_iso(s.end) >= week_ago]

    all_work = _minutes_worked(sessions)
    today_work = _minutes_worked(todays)
    week_work = _minutes_worked(last7)
    completed = len([s for s in sessions if s.planned == PHASE_WORK])

    # Streaks are runs of consecutive work sessions with <2h between them.
    # A gap of 2h+ counts as a streak break.
    ordered = sorted(sessions, key=lambda s: _parse_iso(s.start))
    best_streak = 0
    running = 0
    current_streak = 0
    for s in ordered:
        start_dt = _parse_iso(s.start)
        if running and start_dt - prev_end <= timedelta(hours=2):
            running += 1
        else:
            running = 1
        prev_end = _parse_iso(s.end)
        best_streak = max(best_streak, running)
        if start_dt.date() == today:
            current_streak = running

    def hours(mins: int) -> str:
        return f"{mins // 60}h{mins % 60:02d}" if mins >= 60 else f"{mins}m"

    lines = [
        style("FOCUS TIMER — STATS", COLORS["bold"], COLORS["cyan"]),
        "",
        f"  Today      {hours(today_work):>6}  ·  {len(todays)} session(s)",
        f"  Last 7d    {hours(week_work):>6}  ·  {len(last7)} session(s)",
        f"  All time   {hours(all_work):>6}  ·  {completed} focus session(s)",
        "",
        f"  Best streak        {best_streak} consecutive focus sessions",
        f"  Current streak     {current_streak} consecutive focus sessions",
        "",
        f"  History file: {HISTORY_FILE}",
    ]
    return "\n".join(lines)


def list_today(sessions: list[Session]) -> str:
    today = date.today()
    todays = [s for s in sessions if _parse_iso(s.start).date() == today]
    if not todays:
        return style("Nothing recorded yet today.", COLORS["dim"])

    lines = [style("TODAY'S SESSIONS", COLORS["bold"], COLORS["cyan"])]
    total = 0
    for s in todays:
        start = _parse_iso(s.start)
        end = _parse_iso(s.end)
        dur = round((end - start).total_seconds() / 60)
        total += dur
        label = "work" if s.planned == PHASE_WORK else "break"
        lines.append(
            f"  {start.strftime('%H:%M')}–{end.strftime('%H:%M')}  "
            f"{style(f'{dur:>3}m', COLORS['bold'])}  {label}"
        )
    lines.append("")
    lines.append(f"  Total focus: {total}m across {len(todays)} session(s)")
    return "\n".join(lines)


# --------------------------------------------------------------------------
# The timer itself
# --------------------------------------------------------------------------


def _render_timer(
    phase: str,
    remaining: timedelta,
    paused: bool,
    cycles_done: int,
    total_minutes: int,
) -> str:
    cols, _ = terminal_size()

    label = PHASE_LABEL[phase]
    color = PHASE_COLOR[phase]
    bar_width = max(10, cols - 14)

    mm = remaining.seconds // 60
    ss = remaining.seconds % 60

    header = (
        style("FOCUS TIMER", COLORS["bold"], COLORS["magenta"])
        + style(f"  ·  {label}", COLORS["bold"], color)
        + style(f"  ·  cycle {cycles_done}", COLORS["dim"])
    )
    clock = style(f"{mm:02d}:{ss:02d}", COLORS["bold"]) + (
        style("  (paused)", COLORS["yellow"]) if paused else ""
    )

    # Progress bar: the phase drains from full to empty as it counts down.
    total_seconds = total_minutes * 60
    remaining_fraction = (
        remaining.total_seconds() / total_seconds if total_seconds > 0 else 0.0
    )
    filled = min(bar_width, max(0, round(bar_width * remaining_fraction)))
    bar_line = color + "▐" + ("█" * filled) + ("░" * (bar_width - filled)) + "▌" + COLORS["reset"]

    focus_today = _minutes_worked(
        [s for s in load_history() if _parse_iso(s.start).date() == date.today()]
    )
    summary = style(
        f"focus today: {focus_today}m   ·   [space] pause   [s] skip   [r] restart   [q] quit",
        COLORS["dim"],
    )
    return "\n".join([header, "", bar_line, "  " + clock, "", summary])


def run_timer(work_minutes: int, break_minutes: int) -> None:
    global _SIGINT_SEEN

    phases = [
        (PHASE_WORK, work_minutes),
        (PHASE_BREAK, break_minutes),
    ]

    signal.signal(signal.SIGINT, _on_sigint)
    print(HIDE_CURSOR, end="", flush=True)

    cycles_done = 0
    try:
        with _RawTTY() as tty:
            while True:
                for phase, minutes in phases:
                    start_time = datetime.now()
                    remaining = timedelta(minutes=minutes)
                    paused = False
                    running = True

                    while running:
                        if _SIGINT_SEEN:
                            _SIGINT_SEEN = False
                            # Treat ctrl-c like 'q'.
                            return

                        key = tty.get_key()
                        if key is not None:
                            if key in (" ", "p"):
                                paused = not paused
                            elif key in ("s", "S"):
                                print(CLEAR_LINE, end="\r")
                                print(
                                    style(
                                        f"  Skipped {PHASE_LABEL[phase].lower()}.",
                                        COLORS["yellow"],
                                    ),
                                    end="\r",
                                )
                                print()
                                running = False
                                break
                            elif key in ("r", "R"):
                                remaining = timedelta(minutes=minutes)
                                paused = False
                            elif key in ("q", "Q"):
                                return

                        if paused:
                            print(CLEAR_LINE, end="\r")
                            print(
                                _render_timer(phase, remaining, True, cycles_done, minutes),
                                end="\r",
                            )
                            time.sleep(0.2)
                            continue

                        time.sleep(0.2)
                        remaining -= timedelta(seconds=0.2)

                        if remaining <= timedelta(0):
                            remaining = timedelta(0)
                            end_time = datetime.now()
                            if phase == PHASE_WORK:
                                record(
                                    Session(
                                        start=start_time.isoformat(timespec="seconds"),
                                        end=end_time.isoformat(timespec="seconds"),
                                        minutes=work_minutes,
                                        planned=phase,
                                    )
                                )
                            cycles_done += 1
                            print(CLEAR_LINE, end="\r")
                            print(
                                _render_timer(phase, remaining, False, cycles_done, minutes),
                                end="\r",
                            )
                            print()
                            print(
                                style(
                                    f"  {PHASE_LABEL[phase]} complete."
                                    + (
                                        f" Time for a {break_minutes}m break."
                                        if phase == PHASE_WORK
                                        else " Back to focus."
                                    )
                                ),
                                end="",
                            )
                            print()
                            print()
                            _bell()
                            running = False
                            break

                        print(CLEAR_LINE, end="\r")
                        print(
                            _render_timer(phase, remaining, False, cycles_done, minutes),
                            end="\r",
                        )
    finally:
        print(SHOW_CURSOR, end="", flush=True)
        print()
        print("Session ended. See you next time!")


# --------------------------------------------------------------------------
# CLI entry point
# --------------------------------------------------------------------------


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="focus_timer",
        description="A zero-dependency terminal focus timer.",
        epilog=f"Data is stored in {HISTORY_FILE}.",
    )
    parser.add_argument(
        "minutes",
        nargs="?",
        type=int,
        default=25,
        help="focus length in minutes (default: 25)",
    )
    parser.add_argument(
        "break_minutes",
        nargs="?",
        type=int,
        default=5,
        help="break length in minutes (default: 5)",
    )
    parser.add_argument(
        "--stats",
        action="store_true",
        help="show cumulative focus stats and exit",
    )
    parser.add_argument(
        "--list",
        action="store_true",
        help="list today's sessions and exit",
    )
    parser.add_argument(
        "--reset",
        action="store_true",
        help="erase all recorded history and exit",
    )
    parser.add_argument(
        "--version",
        action="version",
        version=f"%(prog)s {VERSION}",
    )

    args = parser.parse_args(argv)

    if args.reset:
        if HISTORY_FILE.exists():
            HISTORY_FILE.unlink()
            print(f"History cleared ({HISTORY_FILE}).")
        else:
            print("Nothing to clear.")
        return 0

    if args.stats:
        print(stats(load_history()))
        return 0

    if args.list:
        print(list_today(load_history()))
        return 0

    if args.minutes < 1 or args.break_minutes < 1:
        parser.error("minutes must be a positive integer")

    print(style(f"Starting: {args.minutes}m focus / {args.break_minutes}m break", COLORS["dim"]))
    run_timer(args.minutes, args.break_minutes)
    return 0


if __name__ == "__main__":
    sys.exit(main())
