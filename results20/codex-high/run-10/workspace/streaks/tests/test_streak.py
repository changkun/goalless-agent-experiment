import unittest
from datetime import date

from streaks.streak import current_streak, longest_streak


class CurrentStreakTest(unittest.TestCase):
    def test_empty(self):
        self.assertEqual(current_streak([]), 0)

    def test_today_checked_extends(self):
        today = date(2026, 8, 3)
        days = ["2026-07-31", "2026-08-01", "2026-08-02", "2026-08-03"]
        self.assertEqual(current_streak(days, today=today), 4)

    def test_breaks_when_yesterday_missing(self):
        today = date(2026, 8, 3)
        days = ["2026-08-03", "2026-08-01"]
        self.assertEqual(current_streak(days, today=today), 1)

    def test_counts_from_last_checked_when_today_missing(self):
        today = date(2026, 8, 3)
        days = ["2026-08-01", "2026-08-02"]
        self.assertEqual(current_streak(days, today=today), 2)

    def test_history_without_recent_days(self):
        today = date(2026, 8, 3)
        days = ["2026-06-01", "2026-06-02", "2026-06-03"]
        self.assertEqual(current_streak(days, today=today), 0)


class LongestStreakTest(unittest.TestCase):
    def test_empty(self):
        self.assertEqual(longest_streak([]), 0)

    def test_single_run(self):
        days = ["2026-08-01", "2026-08-02", "2026-08-03"]
        self.assertEqual(longest_streak(days), 3)

    def test_ignores_duplicates(self):
        days = ["2026-08-01", "2026-08-01", "2026-08-02", "2026-08-01"]
        self.assertEqual(longest_streak(days), 2)

    def test_picks_longest_run(self):
        days = ["2026-08-01", "2026-08-02", "2026-08-05", "2026-08-06", "2026-08-07"]
        self.assertEqual(longest_streak(days), 3)


if __name__ == "__main__":
    unittest.main()
