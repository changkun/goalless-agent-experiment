import os
import tempfile
import unittest

from pomo.core import Session
from pomo.stats import load, report, save


class StatsTest(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.path = os.path.join(self._tmp.name, "stats.json")

    def test_save_and_load_roundtrip(self):
        sessions = [
            Session(task="Write docs", duration_s=1500, completed_at=1700000000.0),
            Session(task="Fix bug", duration_s=1500, completed_at=1700003600.0),
        ]
        save(sessions, self.path)
        self.assertEqual(load(self.path), sessions)

    def test_load_missing_file_returns_empty(self):
        self.assertEqual(load("/nonexistent/stats.json"), [])

    def test_load_tolerates_corrupt_file(self):
        with open(self.path, "w") as fh:
            fh.write("{not valid json")
        self.assertEqual(load(self.path), [])

    def test_report_empty(self):
        self.assertIn("No sessions", report([]))

    def test_report_contains_summary(self):
        sessions = [
            Session(task="a", duration_s=1500, completed_at=1700000000.0),
            Session(task="b", duration_s=1500, completed_at=1700003600.0),
        ]
        text = report(sessions)
        self.assertIn("Total pomodoros: 2", text)
        self.assertIn("Total focus time: 0h 50m", text)
        self.assertIn("pomodoros)", text)


if __name__ == "__main__":
    unittest.main()
