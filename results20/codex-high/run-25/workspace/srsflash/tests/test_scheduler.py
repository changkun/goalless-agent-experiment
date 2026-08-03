import datetime as dt
import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from srsflash.scheduler import Card, Deck  # noqa: E402


class SchedulerTests(unittest.TestCase):
    def test_new_card_is_due(self):
        card = Card("front", "back")
        self.assertTrue(card.is_due())

    def test_sm2_first_success(self):
        card = Card("front", "back", due=dt.datetime.fromisoformat("2020-01-01T00:00:00+00:00"))
        card.review(5, now=dt.datetime.fromisoformat("2020-01-01T00:00:00+00:00"))
        self.assertEqual(card.repetitions, 1)
        self.assertEqual(card.interval_days, 1)
        self.assertEqual(card.due.day, 2)

    def test_sm2_second_success(self):
        card = Card("front", "back", repetitions=1, interval_days=1)
        card.review(4, now=dt.datetime.fromisoformat("2020-01-02T00:00:00+00:00"))
        self.assertEqual(card.repetitions, 2)
        self.assertEqual(card.interval_days, 6)

    def test_sm2_lapse_resets(self):
        card = Card("front", "back", repetitions=5, interval_days=60, ease=2.5)
        card.review(1, now=dt.datetime.fromisoformat("2020-01-01T00:00:00+00:00"))
        self.assertEqual(card.repetitions, 0)
        self.assertEqual(card.interval_days, 1)
        self.assertEqual(card.due.day, 2)

    def test_ease_never_below_floor(self):
        card = Card("front", "back", ease=1.3)
        card.review(0)
        self.assertGreaterEqual(card.ease, 1.3)

    def test_quality_bounds(self):
        card = Card("front", "back")
        with self.assertRaises(ValueError):
            card.review(6)

    def test_roundtrip_serialization(self):
        with tempfile.TemporaryDirectory() as d:
            path = os.path.join(d, "deck.json")
            deck = Deck(path)
            deck.add("Q", "A")
            deck.save()
            reloaded = Deck(path)
            self.assertEqual(len(reloaded.cards), 1)
            self.assertEqual(reloaded.cards[0].front, "Q")
            self.assertEqual(reloaded.cards[0].back, "A")

    def test_due_filter(self):
        with tempfile.TemporaryDirectory() as d:
            path = os.path.join(d, "deck.json")
            deck = Deck(path)
            past = Card("cold", "card", due=dt.datetime.fromisoformat("2020-01-01T00:00:00+00:00"))
            future = Card("warm", "card", due=dt.datetime.fromisoformat("2999-01-01T00:00:00+00:00"))
            deck.cards = [past, future]
            now = dt.datetime.fromisoformat("2021-01-01T00:00:00+00:00")
            self.assertEqual([c.front for c in deck.due_cards(now)], ["cold"])


if __name__ == "__main__":
    unittest.main()
