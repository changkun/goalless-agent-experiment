import random
import unittest
from datetime import date

from wordle_cli.game import (
    WORD_LEN,
    Game,
    daily_word,
    is_valid,
    random_word,
    score,
)
from wordle_cli.words import VALID_WORDS


class WordListTest(unittest.TestCase):
    def test_entries_valid(self):
        for w in VALID_WORDS:
            self.assertEqual(len(w), WORD_LEN)
            self.assertTrue(w.isalpha())
            self.assertEqual(w, w.lower())


class ScoreTest(unittest.TestCase):
    def test_all_green(self):
        r = score("crane", "crane")
        self.assertEqual(r.colors, ["green"] * 5)
        self.assertTrue(r.is_correct)

    def test_all_grey(self):
        r = score("aaaaa", "bbbbb")
        self.assertEqual(r.colors, ["grey"] * 5)
        self.assertFalse(r.is_correct)

    def test_mixed(self):
        self.assertEqual(score("crate", "crane").colors,
                         ["green", "green", "green", "grey", "green"])

    def test_misplaced_yellow(self):
        r = score("rates", "crane")
        self.assertEqual(r.colors, ["yellow", "yellow", "grey", "yellow", "grey"])

    def test_duplicate_handling(self):
        self.assertEqual(score("lever", "level").colors,
                         ["green", "green", "green", "green", "grey"])

    def test_duplicates_not_double_awarded(self):
        # elder has two e's; eerie has three e's
        self.assertEqual(score("eerie", "elder").colors,
                         ["green", "yellow", "yellow", "grey", "grey"])


class GameTest(unittest.TestCase):
    def test_win(self):
        g = Game("crane")
        g.submit("crane")
        self.assertTrue(g.won)
        self.assertTrue(g.over)

    def test_invalid_rejected(self):
        g = Game("crane")
        with self.assertRaises(ValueError):
            g.submit("xyzzy")
        self.assertEqual(g.guesses, [])

    def test_runs_out_of_guesses(self):
        g = Game("crane")
        for _ in range(g.max_guesses):
            g.submit("robot")
        self.assertTrue(g.over)
        self.assertFalse(g.won)

    def test_remembers_guesses(self):
        g = Game("crane")
        g.submit("robot")
        self.assertEqual(len(g.guesses), 1)
        self.assertEqual(g.guesses_left, g.max_guesses - 1)

    def test_guesses_blocked_after_game_over(self):
        g = Game("crane")
        g.submit("crane")
        with self.assertRaises(ValueError):
            g.submit("robot")

    def test_bad_answer_rejected(self):
        with self.assertRaises(ValueError):
            Game("toolong")


class RandomDailyTest(unittest.TestCase):
    def test_random_word_valid(self):
        for _ in range(100):
            self.assertTrue(is_valid(random_word(random.Random(1))))

    def test_daily_word_deterministic(self):
        d = date(2024, 1, 15)
        self.assertEqual(daily_word(d), daily_word(d))
        self.assertEqual(len(daily_word(d)), WORD_LEN)


if __name__ == "__main__":
    unittest.main()
