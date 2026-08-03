import unittest

from game import (
    Feedback,
    Wordle,
    format_feedback,
    is_correct,
    score_guess,
)


class ScoreGuessTest(unittest.TestCase):
    def test_all_correct(self):
        self.assertEqual(
            score_guess("APPLE", "APPLE"),
            [Feedback.CORRECT] * 5,
        )

    def test_all_absent(self):
        self.assertEqual(
            score_guess("BRAVE", "GHOST"),
            [Feedback.ABSENT] * 5,
        )

    def test_wrong_position(self):
        self.assertEqual(
            score_guess("CRANE", "EAGLE"),
            [Feedback.ABSENT, Feedback.ABSENT, Feedback.PRESENT,
             Feedback.ABSENT, Feedback.CORRECT],
        )

    def test_duplicate_handling_no_overcount(self):
        # Only one 'E' and one 'R' in answer; guess repeats both.
        self.assertEqual(
            score_guess("EERIE", "RIVER"),
            [Feedback.PRESENT, Feedback.ABSENT, Feedback.PRESENT,
             Feedback.PRESENT, Feedback.ABSENT],
        )

    def test_len_mismatch_raises(self):
        with self.assertRaises(ValueError):
            score_guess("ABCD", "ABCDE")

    def test_case_insensitive(self):
        self.assertEqual(
            score_guess("apple", "APPLE"),
            [Feedback.CORRECT] * 5,
        )


class WordleTest(unittest.TestCase):
    def test_valid_word(self):
        self.assertEqual(Wordle.from_word("apple").answer, "APPLE")

    def test_invalid_length(self):
        with self.assertRaises(ValueError):
            Wordle.from_word("cat")

    def test_invalid_characters(self):
        with self.assertRaises(ValueError):
            Wordle.from_word("app1e")


class ResultHelpersTest(unittest.TestCase):
    def test_is_correct_true_and_false(self):
        self.assertTrue(is_correct([Feedback.CORRECT] * 5))
        self.assertFalse(is_correct([Feedback.PRESENT] * 5))

    def test_format_feedback_contains_colors(self):
        out = format_feedback([Feedback.CORRECT, Feedback.PRESENT, Feedback.ABSENT] * 1)
        self.assertIn("32", out)
        self.assertIn("33", out)
        self.assertIn("90", out)


if __name__ == "__main__":
    unittest.main()
