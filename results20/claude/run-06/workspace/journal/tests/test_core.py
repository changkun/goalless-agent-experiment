"""Tests for journal.core — pure logic, no filesystem, stdlib unittest."""

import unittest
from datetime import date

from journal.core import Journal


def j(data=None, today="2026-08-03"):
    return Journal(data, today=date.fromisoformat(today))


class TestEntries(unittest.TestCase):
    def test_add_entry_and_read_back(self):
        log = j()
        log.add_entry("wrote some code")
        self.assertEqual(log.entries_for(date(2026, 8, 3)), ["wrote some code"])

    def test_add_entry_for_specific_day(self):
        log = j()
        log.add_entry("first", date(2026, 8, 1))
        log.add_entry("second", date(2026, 8, 1))
        self.assertEqual(log.entries_for(date(2026, 8, 1)), ["first", "second"])

    def test_empty_day_has_no_entries(self):
        self.assertEqual(j().entries_for(date(2026, 8, 3)), [])


class TestHabits(unittest.TestCase):
    def test_add_habit_trims_and_dedups(self):
        log = j()
        log.add_habit("  run  ")
        self.assertEqual(log.habit_names(), ["run"])
        log.add_habit("run")
        self.assertEqual(log.habit_names(), ["run"])

    def test_empty_habit_name_rejected(self):
        with self.assertRaises(ValueError):
            j().add_habit("   ")

    def test_done_records_once_and_sorted(self):
        log = j()
        log.add_habit("run")
        log.done("run", date(2026, 8, 1))
        log.done("run", date(2026, 8, 1))
        log.done("run", date(2026, 8, 2))
        self.assertEqual(log.data["habits"]["run"]["days"], ["2026-08-01", "2026-08-02"])

    def test_done_unknown_habit_raises(self):
        with self.assertRaises(KeyError):
            j().done("nope")


class TestStreaks(unittest.TestCase):
    def test_streak_continuous(self):
        log = j()
        log.add_habit("read")
        for d in range(1, 4):
            log.done("read", date(2026, 8, d))
        self.assertEqual(log.streak("read"), 3)

    def test_streak_counts_back_from_yesterday_when_today_unmarked(self):
        log = j()
        log.add_habit("read")
        log.done("read", date(2026, 8, 1))
        log.done("read", date(2026, 8, 2))
        self.assertEqual(log.streak("read"), 2)

    def test_streak_breaks_on_gap(self):
        log = j()
        log.add_habit("read")
        log.done("read", date(2026, 8, 1))
        log.done("read", date(2026, 8, 3))
        self.assertEqual(log.streak("read"), 1)

    def test_streak_unknown_or_empty_is_zero(self):
        self.assertEqual(j().streak("nope"), 0)

    def test_streak_after_last_doing_day(self):
        log = j()
        log.add_habit("run")
        log.done("run", date(2026, 8, 2))
        log.done("run", date(2026, 8, 3))
        self.assertEqual(log.streak("run"), 2)


class TestStats(unittest.TestCase):
    def test_total_markers(self):
        log = j()
        log.add_habit("a")
        log.add_habit("b")
        log.done("a", date(2026, 8, 1))
        log.done("a", date(2026, 8, 2))
        log.done("b", date(2026, 8, 2))
        self.assertEqual(log.total_markers(), 3)

    def test_active_days_merges_entries_and_habit_days(self):
        log = j()
        log.add_habit("a")
        log.add_entry("x", date(2026, 8, 3))
        log.done("a", date(2026, 8, 1))
        self.assertEqual(list(log.active_days()), ["2026-08-01", "2026-08-03"])


if __name__ == "__main__":
    unittest.main()
