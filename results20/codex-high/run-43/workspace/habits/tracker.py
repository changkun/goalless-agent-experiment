"""Habit and streak tracking core logic."""

from __future__ import annotations

import json
from collections.abc import Iterable
from datetime import date, timedelta
from pathlib import Path

DEFAULT_STORE = Path("habits.json")


class Habit:
    """A single habit with its checked-off dates."""

    def __init__(self, name: str, checkins: set[date] | None = None) -> None:
        self.name = name
        self.checkins: set[date] = set(checkins or ())

    # -- mutations -----------------------------------------------------------
    def check_in(self, day: date) -> None:
        """Record a check-in for ``day`` (idempotent)."""
        self.checkins.add(day)

    def uncheck(self, day: date) -> None:
        """Remove a check-in for ``day`` (no-op if absent)."""
        self.checkins.discard(day)

    # -- queries -------------------------------------------------------------
    def is_checked(self, day: date) -> bool:
        return day in self.checkins

    def total_days(self) -> int:
        """Total number of check-in days (not necessarily consecutive)."""
        return len(self.checkins)

    def streak(self, as_of: date | None = None) -> int:
        """Length of the current run of consecutive check-ins ending today.

        A streak survives a reasonable grace period: a missing today does not
        break yesterday's streak, but a gap of two or more days does.
        """
        as_of = as_of or date.today()
        if self.is_checked(as_of):
            cursor = as_of
        elif self.is_checked(as_of - timedelta(days=1)):
            cursor = as_of - timedelta(days=1)
        else:
            return 0

        count = 0
        while self.is_checked(cursor):
            count += 1
            cursor -= timedelta(days=1)
        return count

    def longest_streak(self) -> int:
        """Longest run of consecutive check-ins ever recorded."""
        days = sorted(self.checkins)
        longest = current = 0
        previous: date | None = None
        for day in days:
            if previous is not None and day - previous == timedelta(days=1):
                current += 1
            else:
                current = 1
            longest = max(longest, current)
            previous = day
        return longest

    # -- (de)serialization ----------------------------------------------------
    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "checkins": sorted(day.isoformat() for day in self.checkins),
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Habit":
        return cls(
            name=str(data["name"]),
            checkins={date.fromisoformat(raw) for raw in data.get("checkins", ())},
        )


def _parse_dates(values: Iterable[date | str]) -> set[date]:
    parsed: set[date] = set()
    for value in values:
        parsed.add(value if isinstance(value, date) else date.fromisoformat(value))
    return parsed


class Tracker:
    """Collection of habits persisted to a JSON file."""

    def __init__(self, store: Path = DEFAULT_STORE) -> None:
        self.store = Path(store)
        self.habits: dict[str, Habit] = {}
        self._load()

    def add(self, name: str, checkins: Iterable[date | str] = ()) -> Habit:
        self._ensure_unique(name)
        habit = Habit(name, _parse_dates(checkins))
        self.habits[name] = habit
        self._save()
        return habit

    def get(self, name: str) -> Habit | None:
        return self.habits.get(name)

    def remove(self, name: str) -> bool:
        removed = self.habits.pop(name, None) is not None
        if removed:
            self._save()
        return removed

    def names(self) -> list[str]:
        return sorted(self.habits)

    def check_in(self, name: str, day: date | None = None) -> Habit:
        habit = self._require(name)
        habit.check_in(day or date.today())
        self._save()
        return habit

    def uncheck(self, name: str, day: date | None = None) -> Habit:
        habit = self._require(name)
        habit.uncheck(day or date.today())
        self._save()
        return habit

    # -- internals -----------------------------------------------------------
    def _require(self, name: str) -> Habit:
        if name not in self.habits:
            raise KeyError(f"no habit named {name!r}")
        return self.habits[name]

    def _ensure_unique(self, name: str) -> None:
        if name in self.habits:
            raise ValueError(f"habit {name!r} already exists")

    def _load(self) -> None:
        if not self.store.exists():
            return
        payload = json.loads(self.store.read_text())
        for item in payload.get("habits", ()):
            habit = Habit.from_dict(item)
            self.habits[habit.name] = habit

    def _save(self) -> None:
        payload = {
            "habits": [habit.to_dict() for habit in self.habits.values()],
        }
        self.store.write_text(
            json.dumps(payload, indent=2, sort_keys=True) + "\n"
        )
