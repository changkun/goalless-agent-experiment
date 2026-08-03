"""Tests for the habit store and streak logic."""

import tempfile
import unittest
from datetime import date, timedelta
from pathlib import Path

from habits.store import Habit, Store


def days_back(count: int) -> date:
    return date.today() - timedelta(days=count)


class TestStreak(unittest.TestCase):
    def test_today_completed(self):
        h = Habit(name="run", created=date.today())
        h.completions.update({days_back(0), days_back(1), days_back(2)})
        self.assertEqual(h.streak(), 3)

    def test_streak_breaks(self):
        h = Habit(name="run", created=date.today())
        h.completions.update({days_back(0), days_back(1), days_back(3)})
        self.assertEqual(h.streak(), 2)

    def test_missed_today_counts_yesterday(self):
        h = Habit(name="run", created=date.today())
        h.completions.update({days_back(1), days_back(2)})
        self.assertEqual(h.streak(), 2)

    def test_no_completions(self):
        h = Habit(name="run", created=date.today())
        self.assertEqual(h.streak(), 0)


class TestStore(unittest.TestCase):
    def _store(self):
        tmp = tempfile.mkdtemp()
        return Store(Path(tmp) / "habits.json")

    def test_roundtrip(self):
        store = self._store()
        store.add("Read")
        store.complete("Read")
        self.assertEqual(store.get("Read").streak(), 1)

        store2 = Store(store.path)
        self.assertEqual(store2.get("Read").total, 1)

    def test_duplicate_add_raises(self):
        store = self._store()
        store.add("Meditate")
        with self.assertRaises(ValueError):
            store.add("Meditate")

    def test_remove(self):
        store = self._store()
        store.add("Write")
        store.remove("Write")
        self.assertIsNone(store.get("Write"))

    def test_complete_key_normalizes_case(self):
        store = self._store()
        store.add("Morning Run")
        habit = store.complete("morning run")
        self.assertEqual(habit.streak(), 1)

    def test_undo(self):
        store = self._store()
        store.add("Stretch")
        store.complete("Stretch")
        store.uncomplete("Stretch")
        self.assertEqual(store.get("Stretch").total, 0)


if __name__ == "__main__":
    unittest.main()
