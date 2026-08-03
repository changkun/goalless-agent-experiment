"""Core data layer for the habit tracker.

Uses plain JSON for storage so the tool has zero external dependencies.
"""
from __future__ import annotations

import json
import os
import tempfile
from datetime import date, datetime, timedelta


def today_iso() -> str:
    """Return today's date as an ISO string (YYYY-MM-DD)."""
    return date.today().isoformat()


def parse_date(value: str) -> date:
    """Parse an ISO date string (YYYY-MM-DD), raising ValueError on failure."""
    return datetime.strptime(value, "%Y-%m-%d").date()


class HabitStore:
    """A simple JSON-backed collection of habits with completion history."""

    def __init__(self, path: str) -> None:
        self.path = path
        self._habits: dict[str, set[str]] = {}
        self._load()

    def _load(self) -> None:
        if not os.path.exists(self.path):
            return
        try:
            with open(self.path, "r", encoding="utf-8") as fh:
                raw = json.load(fh)
        except (json.JSONDecodeError, OSError):
            return
        if not isinstance(raw, dict):
            return
        for name, dates in raw.items():
            if isinstance(name, str) and isinstance(dates, list):
                self._habits[name] = {
                    d for d in dates if isinstance(d, str) and _is_iso(d)
                }

    def save(self) -> None:
        data = {name: sorted(dates) for name, dates in self._habits.items()}
        directory = os.path.dirname(self.path) or "."
        os.makedirs(directory, exist_ok=True)
        tmp_fd, tmp_path = tempfile.mkstemp(dir=directory, prefix=".habits-", suffix=".tmp")
        try:
            with os.fdopen(tmp_fd, "w", encoding="utf-8") as fh:
                json.dump(data, fh, indent=2, sort_keys=True)
            os.replace(tmp_path, self.path)
        finally:
            if os.path.exists(tmp_path):
                os.remove(tmp_path)

    # -- habit management ------------------------------------------------
    def add(self, name: str) -> bool:
        """Create a habit. Returns True if it was newly created."""
        name = name.strip()
        if not name:
            raise ValueError("Habit name cannot be empty.")
        if name in self._habits:
            return False
        self._habits[name] = set()
        return True

    def remove(self, name: str) -> bool:
        """Delete a habit and its history. Returns True if it existed."""
        if name not in self._habits:
            return False
        del self._habits[name]
        return True

    def names(self) -> list[str]:
        return sorted(self._habits)

    # -- completion ------------------------------------------------------
    def check_off(self, name: str, when: str | None = None) -> bool:
        """Mark a habit complete on a given day (defaults to today)."""
        if name not in self._habits:
            return False
        if when is None:
            when = today_iso()
        self._habits[name].add(when)
        return True

    def uncheck(self, name: str, when: str | None = None) -> bool:
        """Remove a completion mark for a habit on a given day."""
        if name not in self._habits:
            return False
        if when is None:
            when = today_iso()
        dates = self._habits[name]
        if when not in dates:
            return False
        dates.discard(when)
        return True

    def completions(self, name: str) -> set[str]:
        return set(self._habits.get(name, set()))

    # -- stats -----------------------------------------------------------
    def current_streak(self, name: str, end: str | None = None) -> int:
        """Number of consecutive days completed ending today (or `end`)."""
        done = self._habits.get(name)
        if not done:
            return 0
        end_date = parse_date(end) if end else date.today()
        cursor = end_date
        streak = 0
        while cursor.isoformat() in done:
            streak += 1
            cursor -= timedelta(days=1)
        return streak

    def longest_streak(self, name: str) -> int:
        """Longest run of consecutive completed days ever recorded."""
        done = self._habits.get(name)
        if not done:
            return 0
        seen = [parse_date(d) for d in done]
        seen.sort()
        longest = 0
        run = 0
        prev = None
        for d in seen:
            if prev is not None and d == prev + timedelta(days=1):
                run += 1
            else:
                run = 1
            longest = max(longest, run)
            prev = d
        return longest

    def total_completions(self, name: str) -> int:
        return len(self._habits.get(name, set()))


def _is_iso(value: str) -> bool:
    try:
        parse_date(value)
        return True
    except ValueError:
        return False
