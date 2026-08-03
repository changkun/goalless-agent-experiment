#!/usr/bin/env python3
"""pomo — a friendly Pomodoro focus timer for the terminal.

Dependency-free (stdlib only). Features:

    * Configurable work / short-break / long-break durations and rounds
    * A clean full-refresh countdown TUI with a progress bar
    * Keyboard controls while running: [p] pause, [r] resume, [s] skip, [q] quit
    * Desktop notifications + terminal bell on phase changes (best-effort)
    * Persistent session log (~/.pomo/log.jsonl) so you can see your stats
    * No curses / colour libs required — uses ANSI codes guarded by isatty

Run `pomo --help` for usage.
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import signal
import sys
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

# --- Configuration ---------------------------------------------------------

CONFIG_PATH = Path(os.environ.get("POMO_CONFIG", Path.home() / ".pomo" / "config.json"))
LOG_PATH = CONFIG_PATH.parent / "log.jsonl"

_DEFAULTS = {
    "work": 25,
    "short": 5,
    "long": 15,
    "rounds": 4,  # short breaks per long-break cycle
}


def _deep_merge(base: dict, override: dict) -> dict:
    out = dict(base)
    for k, v in override.items():
        if isinstance(v, dict) and isinstance(out.get(k), dict):
            out[k] = _deep_merge(out[k], v)
        else:
            out[k] = v
    return out


def load_config() -> dict:
    """Load the config file, overriding baked-in defaults. Mutates nothing."""
    cfg = dict(_DEFAULTS)
    if CONFIG_PATH.exists():
        try:
            loaded = json.loads(CONFIG_PATH.read_text())
            cfg = _deep_merge(cfg, loaded)
        except (json.JSONDecodeError, OSError) as exc:
            print(f"warning: could not read {CONFIG_PATH}: {exc}", file=sys.stderr)
    return cfg


def save_config(cfg: dict) -> None:
    CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
    CONFIG_PATH.write_text(json.dumps(cfg, indent=2) + "\n")


def _validate_duration(name: str, value: int) -> int:
    try:
        value = int(value)
    except (TypeError, ValueError):
        raise ValueError(f"expected an integer for {name!r}, got {value!r}")
    if value < 1 or value > 180:
        raise ValueError(f"{name!r} must be between 1 and 180 minutes")
    return value


# --- Session log -----------------------------------------------------------

def append_log(entry: dict) -> None:
    """Append one line to the session log. Failures are never fatal to the app."""
    try:
        LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
        with LOG_PATH.open("a") as fh:
            fh.write(json.dumps(entry) + "\n")
    except OSError as exc:
        print(f"warning: could not write log: {exc}", file=sys.stderr)


def read_log() -> list[dict]:
    """Return all log entries (oldest first)."""
    entries = []
    if not LOG_PATH.exists():
        return entries
    for line in LOG_PATH.read_text().splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            entries.append(json.loads(line))
        except json.JSONDecodeError:
            continue
    return entries


def stats() -> dict:
    """Aggregate simple totals from the session log."""
    entries = read_log()
    completed = [e for e in entries if e.get("completed") and e.get("kind") == "work"]
    total_seconds = sum(int(e.get("elapsed_seconds", 0)) for e in completed)
    today = datetime.now(timezone.utc).date().isoformat()
    return {
        "sessions": len(completed),
        "focused_minutes": round(total_seconds / 60, 1),
        "today_sessions": sum(1 for e in completed if e.get("ts", "").startswith(today)),
    }


# --- Terminal helpers -------------------------------------------------------

class Terminal:
    """Thin wrapper around ANSI rendering that degrades gracefully when not a tty."""

    def __init__(self, stream=sys.stdout) -> None:
        self.stream = stream
        self.tty = stream.isatty()

    def _write(self, s: str) -> None:
        self.stream.write(s)
        self.stream.flush()

    def hide_cursor(self) -> None:
        if self.tty:
            self._write("\x1b[?25l")

    def show_cursor(self) -> None:
        if self.tty:
            self._write("\x1b[?25h")

    def clear_line(self) -> None:
        if self.tty:
            self._write("\x1b[2K\r")

    def move_up(self, n: int = 1) -> None:
        if self.tty:
            self._write(f"\x1b[{n}A")

    def bell(self) -> None:
        if self.tty:
            self._write("\x07")


def fmt_clock(total_seconds: int) -> str:
    total_seconds = max(0, int(total_seconds))
    m, s = divmod(total_seconds, 60)
    return f"{m:02d}:{s:02d}"


def progress_bar(fraction: float, width: int) -> str:
    """Render a simple filled bar like '███░░░ 50%'."""
    fraction = max(0.0, min(1.0, fraction))
    filled = int(round(fraction * width))
    bar = "█" * filled + "░" * (width - filled)
    return f"{bar} {int(round(fraction * 100))}%"


# --- Notification -----------------------------------------------------------

def notify(title: str, message: str) -> None:
    """Best-effort desktop notification; swallows all failures."""
    if sys.platform == "darwin":
        cmd = ["osascript", "-e", f'display notification "{message}" with title "{title}"']
    elif sys.platform.startswith("linux"):
        cmd = ["notify-send", title, message]
    else:
        return
    try:
        import subprocess

        subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except (OSError, subprocess.SubprocessError):
        pass


# --- Main timer -------------------------------------------------------------

@dataclass
class Phase:
    kind: str  # 'work' | 'short' | 'long'
    label: str
    minutes: int
    _seconds: Optional[int] = field(default=None, repr=False)

    @property
    def seconds(self) -> int:
        """Phase length in seconds; `_seconds` overrides minutes*60 (for testing/demo)."""
        return self._seconds if self._seconds is not None else self.minutes * 60

    @seconds.setter
    def seconds(self, value: int) -> None:
        self._seconds = value


def build_cycle(cfg: dict) -> list[Phase]:
    """Build the ordered phase list for one full pomodoro cycle."""
    work = _validate_duration("work", cfg["work"])
    short = _validate_duration("short", cfg["short"])
    long_ = _validate_duration("long", cfg["long"])
    rounds = int(cfg["rounds"])
    if rounds < 1 or rounds > 12:
        raise ValueError(f"'rounds' must be between 1 and 12, got {rounds!r}")

    phases: list[Phase] = []
    for i in range(rounds):
        phases.append(Phase("work", "Focus", work))
        if i == rounds - 1:
            phases.append(Phase("long", "Long break", long_))
        else:
            phases.append(Phase("short", "Short break", short))
    return phases


def _read_key(term: Terminal, timeout: float) -> Optional[str]:
    """Read a single key within `timeout` seconds, or None. Only used in tty mode."""
    import select
    import termios
    import tty

    fd = sys.stdin.fileno()
    old = termios.tcgetattr(fd)
    try:
        tty.setcbreak(fd)
        ready, _, _ = select.select([sys.stdin], [], [], timeout)
        if not ready:
            return None
        ch = sys.stdin.read(1)
        return ch.lower()
    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, old)


def run_timer(term: Terminal, phase: Phase, phase_index: int, total_phases: int, cfg: dict) -> bool:
    """Run a single phase's countdown. Returns True if completed naturally, False if skipped.

    `remaining` is the source of truth. Each loop iteration we (1) subtract the
    real elapsed time since the last tick, (2) handle one keypress with a short
    blocking timeout, and (3) redraw. This keeps the countdown time-accurate
    while staying responsive to keys.
    """
    total = phase.seconds
    remaining = total
    paused = False
    carry = 0.0  # fractional seconds not yet counted as a full tick
    last_tick = time.monotonic()
    done = False

    notify(phase.label, f"Starting {phase.kind} — {phase.minutes} min")
    if not term.tty:
        term.bell()

    while remaining > 0:
        now = time.monotonic()
        if not paused:
            carry += now - last_tick
            whole = int(carry)  # whole seconds elapsed since last tick
            if whole:
                remaining = max(0, remaining - whole)
                carry = max(0.0, carry - whole)
        last_tick = now

        if term.tty:
            key = _read_key(term, 0.15)  # blocks up to 150ms for a keypress
            if key == "p":
                paused = True
            elif key == "r":
                paused = False
            elif key == "s":
                done = False
                break
            elif key == "q":
                raise KeyboardInterrupt
        elif not paused:  # the paused branch sleeps below
            time.sleep(1.0)

        _render(term, phase, phase_index, total_phases, remaining, total, paused)
    else:
        done = True  # loop exhausted -> completed naturally

    elapsed = max(0, min(total, total - remaining))
    if phase.kind == "work":
        append_log(
            {
                "ts": datetime.now(timezone.utc).isoformat(),
                "kind": "work",
                "minutes": phase.minutes,
                "completed": done,
                "elapsed_seconds": elapsed,
            }
        )

    if done:
        term.bell()
        notify("Pomodoro complete", f"{phase.label} finished. 🎉")
    else:
        term.bell()
        notify("Pomodoro skipped", f"{phase.label} skipped.")
    return done


def _frame(phase: Phase, phase_index: int, total_phases: int, remaining: int, total: int, paused: bool) -> str:
    w = max(8, shutil.get_terminal_size((80, 24)).columns - 20)
    status = "  PAUSED\n" if paused else ""
    lines = (
        f"  {phase.label}  [{phase_index + 1}/{total_phases}]\n"
        f"  {fmt_clock(remaining)}\n"
        f"  {progress_bar(remaining / total, min(w, 40))}\n"
        f"{status}"
        f"  [p] pause  [r] resume  [s] skip  [q] quit"
    )
    return lines


def _frame_line_count(phase: Phase, paused: bool) -> int:
    return 5 if paused else 4


def _render(term: Terminal, phase: Phase, phase_index: int, total_phases: int, remaining: int, total: int, paused: bool) -> None:
    _paint(term, _frame(phase, phase_index, total_phases, remaining, total, paused),
           _frame_line_count(phase, paused))


def _paint(term: Terminal, frame: str, lines: int) -> None:
    """Write a frame top-down and park the cursor back at its first line."""
    term.clear_line()
    term._write(frame + "\n")
    term.move_up(lines)


# --- Commands ---------------------------------------------------------------

def cmd_run(args: argparse.Namespace, cfg: dict) -> int:
    phases = build_cycle(cfg)
    term = Terminal()
    term.hide_cursor()
    try:
        for i, phase in enumerate(phases):
            _render(term, phase, i, len(phases), phase.seconds, phase.seconds, False)
            completed = run_timer(term, phase, i, len(phases), cfg)
            if completed and i + 1 < len(phases):
                term._write("\n")
                time.sleep(1)
    except KeyboardInterrupt:
        term._write("\nInterrupted — see you next session.\n")
        return 130
    finally:
        term.show_cursor()
        term._write("\n")
    return 0


def cmd_set(args: argparse.Namespace, cfg: dict) -> int:
    updates = {}
    for attr in ("work", "short", "long", "rounds"):
        value = getattr(args, attr)
        if value is not None:
            updates[attr] = _validate_duration(attr, value) if attr != "rounds" else value
    if not updates:
        print("no changes requested. see `pomo set --help`.")
        return 1
    merged = dict(cfg, **updates)
    save_config(merged)
    for k, v in updates.items():
        print(f"  {k}: {cfg.get(k)} -> {v}")
    return 0


def cmd_show(args: argparse.Namespace, cfg: dict) -> int:
    print(f"config file: {CONFIG_PATH}")
    for k in _DEFAULTS:
        print(f"  {k}: {cfg.get(k)}")
    return 0


def cmd_stats(args: argparse.Namespace, cfg: dict) -> int:
    s = stats()
    if not s["sessions"]:
        print("No completed focus sessions logged yet.")
        return 0
    print(f"  completed focus sessions: {s['sessions']}")
    print(f"  total focused time:       {s['focused_minutes']} min")
    print(f"  sessions today:           {s['today_sessions']}")
    return 0


# --- CLI --------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="pomo",
        description="A friendly Pomodoro focus timer for the terminal.",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    run = sub.add_parser("run", help="start a full pomodoro cycle")
    run.set_defaults(func=cmd_run)

    sub.add_parser("show", help="show current configuration")
    sub.add_parser("stats", help="show focus statistics")
    setp = sub.add_parser("set", help="change configuration values (persisted)")
    for attr, help_txt in (
        ("work", "focus length in minutes"),
        ("short", "short break length in minutes"),
        ("long", "long break length in minutes"),
        ("rounds", "number of focus sessions before a long break"),
    ):
        setp.add_argument(f"--{attr}", type=int, help=help_txt)
    setp.set_defaults(func=cmd_set)

    # Wire default funcs for the bare subcommands.
    for name, fn in (("show", cmd_show), ("stats", cmd_stats)):
        sub.choices[name].set_defaults(func=fn)
    return parser


def main(argv: Optional[list[str]] = None) -> int:
    cfg = load_config()
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        return args.func(args, cfg)
    except ValueError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    except BrokenPipeError:
        # Downstream consumer (e.g. `head`) closed the pipe; exit quietly.
        try:
            sys.stdout.close()
        except BrokenPipeError:
            pass
        return 0


if __name__ == "__main__":
    sys.exit(main())
