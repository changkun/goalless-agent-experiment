import json
import tempfile
import unittest
from pathlib import Path

from habit_tracker.core import HabitStore, parse_date, today_iso


class StoreTestCase(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.store = HabitStore(str(Path(self.tmp.name) / "habits.json"))

    def test_add_and_list(self):
        self.assertTrue(self.store.add("Read"))
        self.assertFalse(self.store.add("Read"))
        self.assertEqual(self.store.names(), ["Read"])

    def test_add_empty_name_raises(self):
        with self.assertRaises(ValueError):
            self.store.add("   ")

    def test_check_off_and_stats(self):
        self.store.add("Run")
        self.store.check_off("Run", "2026-08-01")
        self.store.check_off("Run", "2026-08-02")
        self.store.check_off("Run", "2026-08-03")
        self.assertEqual(self.store.total_completions("Run"), 3)
        self.assertEqual(self.store.current_streak("Run", end="2026-08-03"), 3)
        self.assertEqual(self.store.current_streak("Run", end="2026-08-04"), 0)
        self.assertEqual(self.store.longest_streak("Run"), 3)

    def test_streak_breaks_on_gap(self):
        self.store.add("Daily")
        for d in ("2026-08-01", "2026-08-02", "2026-08-04"):
            self.store.check_off("Daily", d)
        self.assertEqual(self.store.current_streak("Daily", end="2026-08-04"), 1)
        self.assertEqual(self.store.longest_streak("Daily"), 2)

    def test_undo_removes_completion(self):
        self.store.add("Hydrate")
        self.store.check_off("Hydrate", "2026-08-03")
        self.assertTrue(self.store.uncheck("Hydrate", "2026-08-03"))
        self.assertEqual(self.store.total_completions("Hydrate"), 0)

    def test_remove(self):
        self.store.add("A")
        self.assertTrue(self.store.remove("A"))
        self.assertFalse(self.store.remove("A"))

    def test_persistence_roundtrip(self):
        path = str(Path(self.tmp.name) / "habits.json")
        s1 = HabitStore(path)
        s1.add("Journal")
        s1.check_off("Journal", today_iso())
        s1.save()

        s2 = HabitStore(path)
        self.assertEqual(s2.names(), ["Journal"])
        self.assertEqual(s2.total_completions("Journal"), 1)

    def test_rejects_malformed_data(self):
        path = Path(self.tmp.name) / "bad.json"
        path.write_text(json.dumps({"ok": [99, "not-a-date"]}))
        store = HabitStore(str(path))
        self.assertEqual(store.names(), ["ok"])
        self.assertEqual(store.total_completions("ok"), 0)

    def test_parse_date_validation(self):
        self.assertEqual(parse_date("2026-08-03").isoformat(), "2026-08-03")
        with self.assertRaises(ValueError):
            parse_date("nope")


if __name__ == "__main__":
    unittest.main()
