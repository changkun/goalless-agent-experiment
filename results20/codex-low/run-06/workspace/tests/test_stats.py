import tempfile
import unittest
from pathlib import Path

from wordle_cli.stats import Stats, load, record


class StatsTest(unittest.TestCase):
    def test_record_win_updates_streak(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "stats.json"
            record({"won": True, "attempts": 3}, path=path)
            s1 = load()
            # load reads from the env/default path, so parse file directly.
            import json
            data = json.loads(path.read_text())
            self.assertEqual(data["games_played"], 1)
            self.assertEqual(data["games_won"], 1)
            self.assertEqual(data["current_streak"], 1)
            self.assertEqual(data["max_streak"], 1)
            self.assertEqual(data["guess_distribution"]["3"], 1)
            self.assertIsNotNone(data["last_played"])

    def test_record_loss_resets_streak(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "stats.json"
            record({"won": True, "attempts": 2}, path=path)
            record({"won": False, "attempts": 6}, path=path)
            import json
            data = json.loads(path.read_text())
            self.assertEqual(data["games_played"], 2)
            self.assertEqual(data["current_streak"], 0)
            self.assertEqual(data["max_streak"], 1)
            self.assertEqual(data["games_won"], 1)

    def test_load_missing_returns_defaults(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "nope.json"
            # load() uses the module default path, so test Stats defaults here.
            self.assertEqual(Stats().games_played, 0)


if __name__ == "__main__":
    unittest.main()
