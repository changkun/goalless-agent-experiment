import tempfile
import unittest
from pathlib import Path

from mnemo.db import Deck, today
from mnemo.sm2 import QUALITY_GOOD, schedule


class DeckTest(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.deck = Deck(Path(self._tmp.name) / "deck.db")

    def tearDown(self):
        self.deck.close()
        self._tmp.cleanup()

    def test_add_and_get_roundtrip(self):
        card_id = self.deck.add("2+2", "4")
        card = self.deck.get(card_id)
        self.assertEqual(card["front"], "2+2")
        self.assertEqual(card["back"], "4")
        self.assertEqual(card["due"], today())

    def test_new_card_is_due(self):
        card_id = self.deck.add("q", "a")
        due = self.deck.due()
        self.assertEqual([c["id"] for c in due], [card_id])

    def test_update_state_persists(self):
        card_id = self.deck.add("q", "a")
        state = self.deck.card_state(self.deck.get(card_id))
        new = schedule(state, QUALITY_GOOD, today())
        self.deck.update_state(card_id, new, today() + new.interval)

        fresh = self.deck.get(card_id)
        self.assertEqual(fresh["interval"], new.interval)
        self.assertEqual(fresh["reps"], 1)
        self.assertEqual(fresh["due"], today() + new.interval)

    def test_due_and_stats(self):
        self.deck.add("a", "1")
        self.deck.add("b", "2")  # both due today

        # Move card b into the future so it isn't due.
        b = self.deck.all()[1]
        self.deck.update_state(b["id"], self.deck.card_state(b),
                               today() + 5)

        due = [c["front"] for c in self.deck.due()]
        self.assertEqual(due, ["a"])

        stats = self.deck.stats()
        self.assertEqual(stats["total"], 2)
        self.assertEqual(stats["due_count"], 1)


if __name__ == "__main__":
    unittest.main()
