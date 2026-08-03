"""Tests for the habit tracker's core logic."""

import tempfile
import unittest
from datetime import date, timedelta
from pathlib import Path

from habits.tracker import Habit, Tracker

TODAY = date(2026, 8, 3)


def days(count: int) -> list[date]:
    return [TODAY - timedelta(days=i) for i in range(count)]


class StreakTests(unittest.TestCase):
    def test_empty_is_zero(self):
        self.assertEqual(Habit("x").streak(TODAY), 0)

    def test_starts_at_one(self):
        self.assertEqual(Habit("x", [TODAY]).streak(TODAY), 1)

    def test_counts_consecutive_days(self):
        self.assertEqual(Habit("x", days(5)).streak(TODAY), 5)

    def test_breaks_on_gap(self):
        habit = Habit("x", [TODAY, TODAY - timedelta(days=2)])
        self.assertEqual(habit.streak(TODAY), 1)

    def test_tolerates_missing_today(self):
        habit = Habit("x", [TODAY - timedelta(days=1), TODAY - timedelta(days=2)])
        self.assertEqual(habit.streak(TODAY), 2)

    def test_resets_after_two_day_gap(self):
        self.assertEqual(Habit("x", [TODAY - timedelta(days=2)]).streak(TODAY), 0)

    def test_longest_streak(self):
        habit = Habit("x", [*days(3), TODAY - timedelta(days=5), TODAY - timedelta(days=6)])
        self.assertEqual(habit.longest_streak(), 3)


class HabitHelperTests(unittest.TestCase):
    def test_check_in_is_idempotent(self):
        habit = Habit("x")
        habit.check_in(TODAY)
        habit.check_in(TODAY)
        self.assertEqual(habit.total_days(), 1)

    def test_uncheck_removes_only_today(self):
        yesterday = TODAY - timedelta(days=1)
        habit = Habit("x", [TODAY, yesterday])
        habit.uncheck(TODAY)
        self.assertFalse(habit.is_checked(TODAY))
        self.assertTrue(habit.is_checked(yesterday))


class TrackerTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.store = Path(self.temp.name) / "store.json"

    def tearDown(self):
        self.temp.cleanup()

    def test_round_trip(self):
        tracker = Tracker(self.store)
        tracker.add("read", checkins=[TODAY, TODAY - timedelta(days=1)])
        restored = Tracker(self.store).get("read")
        self.assertIsNotNone(restored)
        self.assertEqual(restored.name, "read")
        self.assertEqual(restored.checkins, {TODAY, TODAY - timedelta(days=1)})

    def test_add_rejects_duplicate(self):
        tracker = Tracker(self.store)
        tracker.add("run")
        with self.assertRaises(ValueError):
            tracker.add("run")

    def test_unknown_habit_raises_keyerror(self):
        with self.assertRaises(KeyError):
            Tracker(self.store).check_in("swim")

    def test_remove_and_persist(self):
        tracker = Tracker(self.store)
        tracker.add("run")
        self.assertTrue(tracker.remove("run"))
        self.assertFalse(tracker.remove("run"))
        self.assertEqual(Tracker(self.store).names(), [])


if __name__ == "__main__":
    unittest.main()
