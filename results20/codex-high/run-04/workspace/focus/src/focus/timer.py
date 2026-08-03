"""Console Pomodoro timer with countdown and milestone logging."""

from __future__ import annotations

import shutil
import sys
import time
from datetime import timedelta
from typing import Callable

DEFAULT_FOCUS_MIN = 25
DEFAULT_BREAK_MIN = 5


def _fmt(seconds: int) -> str:
    m, s = divmod(max(0, seconds), 60)
    return f"{m:02d}:{s:02d}"


def _bar(pct: float, width: int) -> str:
    if width <= 1:
        return ""
    filled = int(pct * width)
    return "[" + "#" * filled + "-" * (width - filled) + "]"


def _clear_line() -> None:
    if sys.stdout.isatty():
        sys.stdout.write("\r" + " " * shutil.get_terminal_size((80, 24)).columns + "\r")
    else:
        sys.stdout.write("\r")
    sys.stdout.flush()


def _bell() -> None:
    sys.stdout.write("\a")
    sys.stdout.flush()


def run_timer(
    minutes: int,
    label: str,
    on_tick: Callable[[int, str], None] | None = None,
    on_done: Callable[[], None] | None = None,
) -> None:
    """Count down from `minutes`, redrawing a progress line each second."""
    total = minutes * 60
    deadline = time.monotonic() + total
    print(f"▶ {label}  ({minutes} min)")
    try:
        while True:
            remaining = int(deadline - time.monotonic())
            if remaining <= 0:
                break
            if on_tick:
                on_tick(remaining, label)
            else:
                width = max(10, shutil.get_terminal_size((80, 24)).columns - len(_fmt(remaining)) - 12)
                pct = (total - remaining) / total
                _clear_line()
                sys.stdout.write(f"{_fmt(remaining)} {_bar(pct, width)} {label}")
                sys.stdout.flush()
            time.sleep(1)
    except KeyboardInterrupt:
        _clear_line()
        print("Stopped.")
        return
    _clear_line()
    print(f"✓ {label} complete.")
    if on_done:
        on_done()
    else:
        _bell()


def format_session(seconds: int) -> str:
    return str(timedelta(seconds=seconds))
