"""Core logic for the journal CLI.

Everything here is pure and testable: it takes/returns plain data and never
touches the filesystem or user I/O. The CLI layer in ``__main__.py`` handles
persistence and printing.
"""

from __future__ import annotations

from datetime import date, timedelta
from typing import Iterable


class Journal:
    """An in-memory journal: daily entries plus habit check-ins.

    ``data`` is the raw dict that gets serialized to disk. ``today`` is
    injected so streak math is deterministic in tests.
    """

    def __init__(self, data: dict | None = None, today: date | None = None) -> None:
        self.data = data if data is not None else {"entries": {}, "habits": {}}
        self.data.setdefault("entries", {})
        self.data.setdefault("habits", {})
        self.today = today or date.today()

    # ------------------------------------------------------------------ dailies

    def _day(self, d: date) -> str:
        return d.isoformat()

    def add_entry(self, text: str, d: date | None = None) -> list[str]:
        """Append ``text`` to the entry list for the given day (default today)."""
        day = self._day(d or self.today)
        entries = self.data["entries"].setdefault(day, [])
        entries.append(text)
        return entries

    def entries_for(self, d: date) -> list[str]:
        return list(self.data["entries"].get(self._day(d), []))

    # ------------------------------------------------------------------ habits

    def add_habit(self, name: str) -> None:
        name = name.strip()
        if not name:
            raise ValueError("habit name cannot be empty")
        habits = self.data["habits"]
        if name in habits:
            return
        habits[name] = {"days": []}

    def done(self, name: str, d: date | None = None) -> None:
        """Record that ``name`` was done on the given day (default today)."""
        day = self._day(d or self.today)
        habit = self.data["habits"].get(name)
        if habit is None:
            raise KeyError(f"unknown habit: {name!r}")
        if day not in habit["days"]:
            habit["days"].append(day)
            habit["days"].sort()

    def untrack(self, name: str) -> None:
        del self.data["habits"][name]

    def habit_names(self) -> list[str]:
        return sorted(self.data["habits"])

    def streak(self, name: str) -> int:
        """Number of consecutive days (ending today or yesterday) the habit was done.

        A streak counts back from today. If today isn't marked yet, it can still
        count back from yesterday (a "pending today" streak isn't broken until
        today ends). Returns 0 for an unknown or never-done habit.
        """
        days = set(self.data["habits"].get(name, {}).get("days", []))
        if not days:
            return 0

        anchor = self.today
        if self._day(anchor) not in days:
            anchor = anchor - timedelta(days=1)  # today not marked yet

        count = 0
        day = anchor
        while self._day(day) in days:
            count += 1
            day -= timedelta(days=1)
        return count

    def streaks(self) -> dict[str, int]:
        return {name: self.streak(name) for name in self.habit_names()}

    # ------------------------------------------------------------------ stats

    def total_markers(self) -> int:
        return sum(len(h["days"]) for h in self.data["habits"].values())

    def active_days(self) -> Iterable[str]:
        """All distinct days that have at least one entry or habit marker."""
        days = set(self.data["entries"])
        for h in self.data["habits"].values():
            days.update(h["days"])
        return sorted(days)
