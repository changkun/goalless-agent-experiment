"""Persistence layer for the habit tracker.

Data is stored as JSON so it is human-readable and easy to back up or edit.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import date
from pathlib import Path
from typing import Any


def _today() -> date:
    return date.today()


def _prev_day(day: date) -> date:
    return day.fromordinal(day.toordinal() - 1)


@dataclass
class Habit:
    name: str
    created: date
    completions: set[date] = field(default_factory=set)

    @property
    def total(self) -> int:
        return len(self.completions)

    def streak(self, today: date | None = None) -> int:
        """Number of consecutive days completed up to (and including) today."""
        today = today or _today()
        last = today if today in self.completions else _prev_day(today)
        count = 0
        while last in self.completions:
            count += 1
            last = _prev_day(last)
        return count

    def is_done(self, day: date) -> bool:
        return day in self.completions

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "created": self.created.isoformat(),
            "completions": sorted(d.isoformat() for d in self.completions),
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Habit":
        name = str(data["name"])
        created = date.fromisoformat(str(data["created"]))
        completions = {date.fromisoformat(d) for d in data.get("completions", [])}
        return cls(name=name, created=created, completions=completions)


class Store:
    def __init__(self, path: Path | str | None = None) -> None:
        if path is None:
            path = Path.home() / ".habits" / "habits.json"
        self.path = Path(path)

    def _read(self) -> dict[str, Habit]:
        if not self.path.exists():
            return {}
        raw = json.loads(self.path.read_text(encoding="utf-8"))
        return {name: Habit.from_dict(data) for name, data in raw.items()}

    def _write(self, habits: dict[str, Habit]) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        payload = {name: habit.to_dict() for name, habit in habits.items()}
        self.path.write_text(
            json.dumps(payload, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )

    def list(self) -> list[Habit]:
        return list(self._read().values())

    def get(self, name: str) -> Habit | None:
        return self._read().get(self._key(name))

    def add(self, name: str) -> Habit:
        habits = self._read()
        key = self._key(name)
        if key in habits:
            raise ValueError(f"Habit already exists: {name}")
        habit = Habit(name=name, created=_today())
        habits[key] = habit
        self._write(habits)
        return habit

    def complete(self, name: str, day: date | None = None) -> Habit:
        habits = self._read()
        key = self._key(name)
        if key not in habits:
            raise KeyError(f"Unknown habit: {name}")
        habits[key].completions.add(day or _today())
        self._write(habits)
        return habits[key]

    def uncomplete(self, name: str, day: date | None = None) -> Habit:
        habits = self._read()
        key = self._key(name)
        if key not in habits:
            raise KeyError(f"Unknown habit: {name}")
        habits[key].completions.discard(day or _today())
        self._write(habits)
        return habits[key]

    def remove(self, name: str) -> None:
        habits = self._read()
        key = self._key(name)
        if key not in habits:
            raise KeyError(f"Unknown habit: {name}")
        del habits[key]
        self._write(habits)

    @staticmethod
    def _key(name: str) -> str:
        return " ".join(name.strip().lower().split())
