import unittest

from wordle.game import GRAY, GREEN, Wordle, YELLOW
from wordle.words import ANSWERS


class AnswerListTest(unittest.TestCase):
    def test_all_answers_are_five_letters(self):
        for word in ANSWERS:
            self.assertEqual(len(word), 5, f"{word!r} is not 5 letters")
            self.assertTrue(word.isalpha(), f"{word!r} has non-letters")
            self.assertTrue(word.isupper(), f"{word!r} should be uppercase")

    def test_answers_are_unique(self):
        self.assertEqual(len(ANSWERS), len(set(ANSWERS)))


class WordleLogicTest(unittest.TestCase):
    def test_exact_match_wins(self):
        game = Wordle("ROBOT")
        _, pattern = game.guess("robot")
        self.assertEqual(pattern, [GREEN] * 5)
        self.assertTrue(game.won)
        self.assertTrue(game.finished)

    def test_yellow_and_gray(self):
        game = Wordle("ROBOT")
        _, pattern = game.guess("STORE")
        self.assertEqual(pattern[1], YELLOW)   # T present, wrong spot
        self.assertEqual(pattern[2], YELLOW)   # O present, wrong spot
        self.assertEqual(pattern[3], YELLOW)   # R present, wrong spot
        self.assertEqual(pattern[0], GRAY)     # S absent
        self.assertEqual(pattern[4], GRAY)     # E absent
        self.assertFalse(game.won)

    def test_green_takes_priority(self):
        game = Wordle("ROBOT")
        _, pattern = game.guess("ROLLS")
        self.assertEqual(pattern[0], GREEN)    # R in place
        self.assertEqual(pattern[1], GREEN)    # O in place
        self.assertFalse(game.won)

    def test_duplicate_letters_only_count_once(self):
        # Answer has two Os; a guess with more Os marks at most two.
        game = Wordle("ROBOT")
        _, pattern = game.guess("OOOPS")
        self.assertEqual(pattern.count(YELLOW) + pattern.count(GREEN), 2)

    def test_repeated_letter_matching(self):
        game = Wordle("GREEN")
        _, pattern = game.guess("SEEKS")
        # E appears twice in GREEN; two Es in the guess both get marked present.
        self.assertEqual(pattern.count(YELLOW) + pattern.count(GREEN), 2)

    def test_validation(self):
        game = Wordle("ROBOT")
        self.assertIsNotNone(game.validate("tool"))
        self.assertIsNotNone(game.validate("tool1"))
        self.assertIsNone(game.validate("table"))

    def test_max_guesses(self):
        game = Wordle("ROBOT")
        for g in ("AAAAA", "BBBBB", "CCCCC", "DDDDD", "EEEEE", "FFFFF"):
            game.guess(g)
        self.assertTrue(game.finished)
        self.assertFalse(game.won)

    def test_raises_on_bad_guess(self):
        game = Wordle("ROBOT")
        with self.assertRaises(ValueError):
            game.guess("four")


if __name__ == "__main__":
    unittest.main()
