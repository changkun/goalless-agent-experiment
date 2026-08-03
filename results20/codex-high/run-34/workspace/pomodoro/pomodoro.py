#!/usr/bin/env python3
"""drop: a tiny Pomodoro focus timer for the terminal.

Pure Python stdlib. Tracks focus sessions, logs them to a JSON file,
and prints ASCII countdown plus a daily summary.
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from datetime import date, datetime
from pathlib import Path
from typing import Optional

APP_NAME = "drop"
DEFAULTS = {
    "focus": 25 * 60,
    "short": 5 * 60,
    "long": 15 * 60,
    "cycles": 4,
}
STATE_SUFFIX = "drop-state.json"


def _log_dir() -> Path:
    return Path(__import__("os").environ.get("XDG_DATA_HOME", Path.home() / ".local/share")) / APP_NAME


def log_path() -> Path:
    return _log_dir() / "sessions.json"


def state_dir() -> Path:
    return _log_dir() / "state"


def now_iso() -> str:
    return datetime.now().isoformat(timespec="seconds")


# --------------------------------------------------------------------------
# terminal helpers
# --------------------------------------------------------------------------

def bar(fraction: float, width: int = 20) -> str:
    filled = int(round(fraction * width))
    return "[" + "#" * filled + "-" * (width - filled) + "]"


def fmt_remaining(seconds: int) -> str:
    m, s = divmod(max(0, seconds), 60)
    return f"{m:02d}:{s:02d}"


def fmt_duration(seconds: int) -> str:
    seconds = int(seconds)
    if seconds < 60:
        return f"{seconds}s"
    m, s = divmod(seconds, 60)
    if m < 60:
        return f"{m}m{s:02d}s" if s else f"{m}m"
    h, m = divmod(m, 60)
    return f"{h}h{m:02d}m"


def beep() -> None:
    try:
        sys.stdout.write("\a")
        sys.stdout.flush()
    except Exception:
        pass


def render_countdown(label: str, remaining: int, total: int) -> str:
    frac = remaining / total if total else 0
    return f" {label:<7} {bar(frac)} {fmt_remaining(remaining)}"


def clear_line() -> None:
    sys.stdout.write("\r\033[K")
    sys.stdout.flush()


# --------------------------------------------------------------------------
# persistence
# --------------------------------------------------------------------------

def load_sessions() -> list[dict]:
    path = log_path()
    if not path.exists():
        return []
    try:
        data = json.loads(path.read_text())
        return data if isinstance(data, list) else []
    except (json.JSONDecodeError, OSError):
        return []


def append_session(duration: int, kind: str, complete: bool) -> None:
    path = log_path()
    sessions = load_sessions()
    sessions.append(
        {
            "kind": kind,
            "duration": duration,
            "complete": complete,
            "ended_at": now_iso(),
            "date": date.today().isoformat(),
        }
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(sessions, indent=2))


# --------------------------------------------------------------------------
# timer
# --------------------------------------------------------------------------

def run_timer(label: str, seconds: int) -> bool:
    """Run a countdown. Returns True if it finished naturally."""
    end = time.monotonic() + seconds
    remaining = seconds
    try:
        while remaining > 0:
            clear_line()
            sys.stdout.write(render_countdown(label, remaining, seconds))
            sys.stdout.flush()
            # give the user a chance to interrupt
            time.sleep(min(1.0, remaining))
            remaining = int(end - time.monotonic())
        clear_line()
        print(f" {label:<7} done!")
        beep()
        return True
    except KeyboardInterrupt:
        clear_line()
        if remaining > 0:
            answer = input(f"\n {label} paused ({fmt_remaining(remaining)} left). "
                           f"Resume (r), abandon (a), skip (s)? ").strip().lower()
            if answer == "r":
                return run_timer(label, remaining)
            if answer == "a":
                print(f" abandoned {label}. Logged as incomplete.")
                return False
            # 's' or anything else counts as finishing the block
            return True
        return True


# --------------------------------------------------------------------------
# session flow
# --------------------------------------------------------------------------

def pomodoro(count: int, config: dict) -> None:
    print(f" {APP_NAME} · {count} focus {'session' if count == 1 else 'sessions'}\n")
    completed = 0
    focus_done = 0
    for i in range(1, count + 1):
        focus_seconds = config["focus"]
        label = f"focus {i}/{count}"
        ok = run_timer(label, focus_seconds)
        append_session(focus_seconds, "focus", ok)
        focus_done += int(ok)

        if i == count:
            break
        if i % config["cycles"] == 0:
            break_label, break_seconds = "long break", config["long"]
        else:
            break_label, break_seconds = "short break", config["short"]
        ok = run_timer(break_label, break_seconds)
        append_session(break_seconds, "break", ok)

    print(f"\n 🍅 session finished: {focus_done}/{count} focus blocks completed")


# --------------------------------------------------------------------------
# stats
# --------------------------------------------------------------------------

def stats(days: int, today_only: bool) -> None:
    sessions = load_sessions()
    cutoff = date.today().toordinal() - max(0, days - 1)
    rows = [
        s for s in sessions
        if (today_only and s.get("date") == date.today().isoformat())
        or (not today_only and datetime.fromisoformat(s["ended_at"]).date().toordinal() >= cutoff)
    ]
    if not rows:
        print(" no sessions recorded yet.")
        return
    focus = [s for s in rows if s["kind"] == "focus"]
    focus_secs = sum(s["duration"] for s in focus if s["complete"])
    breaks = sum(s["duration"] for s in rows if s["kind"] == "break" and s["complete"])
    print(f" {APP_NAME} · last {days} day(s)\n")
    print(f"   focus blocks completed : {sum(1 for s in focus if s['complete'])}")
    print(f"   focus blocks abandoned : {sum(1 for s in focus if not s['complete'])}")
    print(f"   focus time focused     : {fmt_duration(focus_secs)}")
    print(f"   break time taken       : {fmt_duration(breaks)}")
    incompletes = [s for s in focus if not s["complete"]]
    if incompletes:
        print("\n   abandoned sessions:")
        for s in incompletes:
            print(f"     - {s.get('ended_at', '?')} ({fmt_duration(s['duration'])})")


# --------------------------------------------------------------------------
# cli
# --------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog=APP_NAME,
        description="A tiny terminal Pomodoro timer.",
    )
    parser.add_argument("-f", "--focus", type=int, default=DEFAULTS["focus"],
                        help=f"focus length in minutes (default {DEFAULTS['focus'] // 60})")
    parser.add_argument("-n", "--count", type=int, default=DEFAULTS["cycles"],
                        help=f"number of focus sessions (default {DEFAULTS['cycles']})")
    parser.add_argument("-s", "--short", type=int, default=DEFAULTS["short"] // 60,
                        help=f"short break in minutes (default {DEFAULTS['short'] // 60})")
    parser.add_argument("-l", "--long", type=int, default=DEFAULTS["long"] // 60,
                        help=f"long break in minutes (default {DEFAULTS['long'] // 60})")
    parser.add_argument("--cycles", type=int, default=DEFAULTS["cycles"],
                        help="focus sessions before a long break (default 4)")
    parser.add_argument("--log", action="store_true",
                        help="print session history")
    parser.add_argument("--days", type=int, default=7,
                        help="days of history to show (default 7)")
    parser.add_argument("--today", action="store_true",
                        help="show only today's stats")
    return parser


def main(argv: Optional[list[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.log or args.today:
        stats(args.days, args.today)
        return 0

    if args.focus <= 0 or args.short < 0 or args.long < 0 or args.count <= 0:
        parser.error("durations and counts must be positive")

    config = {
        "focus": args.focus * 60,
        "short": args.short * 60,
        "long": args.long * 60,
        "cycles": args.cycles,
    }
    pomodoro(args.count, config)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
