"""Unit tests for srs.py — run with: python3 -m unittest test_srs -v

Only the pure/scheduling + persistence logic is tested here; the interactive
review prompt is exercised via a small simulated end-to-end test.
"""

import contextlib
import io
import tempfile
import time
import unittest
import unittest.mock
from pathlib import Path

import srs


class TestScheduling(unittest.TestCase):
    def test_first_review_sets_day_1(self):
        self.assertEqual(srs.next_interval(0, 2.5, 4, 0.0), 1.0)

    def test_second_review_six_days(self):
        self.assertEqual(srs.next_interval(1, 2.5, 4, 1.0), 6.0)

    def test_failure_resets_to_day_1_regardless_of_step(self):
        self.assertEqual(srs.next_interval(10, 2.5, 2, 45.0), 1.0)

    def test_interval_grows_with_ease(self):
        # step>=2: interval = last * ease  (grade 4/5)
        self.assertEqual(srs.next_interval(2, 2.5, 4, 6.0), 15.0)
        # hard shortens it
        self.assertEqual(srs.next_interval(2, 2.5, 3, 6.0), 18.0)  # *2.5*1.2

    def test_interval_never_below_min(self):
        self.assertGreaterEqual(srs.next_interval(5, 1.3, 4, 0.5), 1.0)

    def test_ease_decreases_on_fail_and_clamps(self):
        self.assertEqual(srs.updated_ease(0, 2.5), 2.3)
        self.assertEqual(srs.updated_ease(3, 1.4), 1.3)   # clamps at EASE_MIN
        self.assertEqual(srs.updated_ease(5, 2.5), 2.5)   # clamps at EASE_MAX

    def test_ease_increases_on_easy(self):
        self.assertEqual(srs.updated_ease(5, 2.0), 2.15)


class TestStore(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.path = Path(self.tmp.name) / "cards.json"

    def tearDown(self):
        self.tmp.cleanup()

    def test_add_and_get(self):
        s = srs.Store(self.path)
        card = srs.Card(front="q", back="a", deck="d")
        s.add(card)
        self.assertIs(s.get("d", "q"), card)

    def test_persist_roundtrip(self):
        s = srs.Store(self.path)
        s.add(srs.Card(front="q", back="a", deck="d", step=2, ease=2.0, interval=15.0))
        s.deck_names.add("empty")
        s.save()

        s2 = srs.Store(self.path)  # reload
        c = s2.get("d", "q")
        self.assertIsNotNone(c)
        self.assertEqual((c.step, c.ease, c.interval, c.back), (2, 2.0, 15.0, "a"))
        self.assertIn("empty", s2.decks())

    def test_lazy_empty_store_is_valid(self):
        s = srs.Store(self.path)
        s.save()
        s2 = srs.Store(self.path)
        self.assertEqual(s2.cards_for(None), [])

    def test_deck_filtering(self):
        s = srs.Store(self.path)
        s.add(srs.Card("a", "a", "d1"))
        s.add(srs.Card("b", "b", "d2"))
        self.assertEqual([c.front for c in s.cards_for("d1")], ["a"])
        self.assertEqual(len(s.cards_for(None)), 2)


class TestEndToEndReview(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.path = Path(self.tmp.name) / "cards.json"

    def tearDown(self):
        self.tmp.cleanup()

    def test_pass_updates_schedule(self):
        s = srs.Store(self.path)
        s.add(srs.Card(front="q", back="a", deck="d"))

        # Simulate what cmd_review does for grade 4 (good) on day 0.
        now = time.time()
        card = s.get("d", "q")
        card.interval = srs.next_interval(card.step, card.ease, 4, card.interval)
        card.step += 1
        card.due = now + card.interval * 86400
        self.assertEqual(card.step, 1)
        self.assertEqual(card.interval, 1.0)
        s.save()

        s2 = srs.Store(self.path)
        c2 = s2.get("d", "q")
        self.assertEqual((c2.step, c2.interval), (1, 1.0))

    def test_main_add_uses_file_and_prints(self):
        # Use a temp SRS_FILE so we don't touch the cwd.
        src = io.StringIO()
        store_path = self.path
        with contextlib.redirect_stdout(src):
            with unittest.mock.patch.dict("os.environ", {"SRS_FILE": str(store_path)}):
                code = srs.main(["add", "hello", "world", "greetings"])
        self.assertEqual(code, 0)
        self.assertIn("greetings", src.getvalue())
        s = srs.Store(store_path)
        self.assertEqual(s.get("greetings", "hello").back, "world")


if __name__ == "__main__":
    unittest.main()
