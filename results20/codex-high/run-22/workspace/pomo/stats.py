"""Persistent session statistics stored as JSON."""
from __future__ import annotations

import json
import os
from collections import defaultdict
from datetime import datetime

from .core import Session

DEFAULT_PATH = os.path.join(os.path.expanduser("~"), ".pomo-stats.json")


def _date(ts: float) -> str:
    return datetime.fromtimestamp(ts).strftime("%Y-%m-%d")


def load(path: str = DEFAULT_PATH) -> list[Session]:
    """Load sessions from the JSON store, tolerating missing/corrupt data."""
    if not os.path.exists(path):
        return []
    try:
        with open(path, "r", encoding="utf-8") as fh:
            data = json.load(fh)
    except (OSError, json.JSONDecodeError):
        return []
    sessions = []
    for item in data:
        try:
            sessions.append(
                Session(
                    task=item["task"],
                    duration_s=int(item["duration_s"]),
                    completed_at=float(item["completed_at"]),
                )
            )
        except (KeyError, TypeError, ValueError):
            continue
    return sessions


def save(sessions: list[Session], path: str = DEFAULT_PATH) -> None:
    """Write sessions to the JSON store atomically."""
    data = [
        {
            "task": s.task,
            "duration_s": s.duration_s,
            "completed_at": s.completed_at,
        }
        for s in sessions
    ]
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as fh:
        json.dump(data, fh, indent=2)
    os.replace(tmp, path)


def report(sessions: list[Session]) -> str:
    """Build a human-readable summary from a list of sessions."""
    if not sessions:
        return "No sessions recorded yet."
    total_s = sum(s.duration_s for s in sessions)
    by_day: dict[str, int] = defaultdict(int)
    for s in sessions:
        by_day[_date(s.completed_at)] += s.duration_s
    lines = [
        f"Total pomodoros: {len(sessions)}",
        f"Total focus time: {total_s // 3600}h {total_s % 3600 // 60}m",
        "Focus time by day:",
    ]
    for day in sorted(by_day):
        secs = by_day[day]
        lines.append(
            f"  {day}: {secs // 3600}h {secs % 3600 // 60}m " f"({secs // (25 * 60)} pomodoros)"
        )
    return "\n".join(lines)
