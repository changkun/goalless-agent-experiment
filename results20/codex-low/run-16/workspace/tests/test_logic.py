import io
import unittest

from wordle import logic


class EvaluateTests(unittest.TestCase):
    def test_all_correct(self):
        self.assertEqual(logic.evaluate("crane", "crane"),
                         [logic.CORRECT] * 5)

    def test_misplaced_letter(self):
        self.assertEqual(logic.evaluate("crane", "crate"),
                         [logic.CORRECT, logic.CORRECT, logic.CORRECT,
                          logic.ABSENT, logic.CORRECT])

    def test_absent_letter(self):
        self.assertEqual(logic.evaluate("xxxxx", "crane"),
                         [logic.ABSENT] * 5)

    def test_repeated_letter_only_credited_once(self):
        # Only one 'a' in answer; second 'a' must not be present.
        self.assertEqual(logic.evaluate("alarm", "acorn"),
                         [logic.CORRECT, logic.ABSENT, logic.ABSENT,
                          logic.CORRECT, logic.ABSENT])

    def test_repeated_letter_with_matching_position(self):
        # 'a' matches at position 0; the 'l' matches elsewhere.
        self.assertEqual(logic.evaluate("allay", "ample"),
                         [logic.CORRECT, logic.PRESENT, logic.ABSENT,
                          logic.ABSENT, logic.ABSENT])

    def test_different_length_raises(self):
        with self.assertRaises(ValueError):
            logic.evaluate("cran", "crane")


class IsValidGuessTests(unittest.TestCase):
    def test_valid(self):
        self.assertTrue(logic.is_valid_guess("crane"))

    def test_too_short(self):
        self.assertFalse(logic.is_valid_guess("cran"))

    def test_too_long(self):
        self.assertFalse(logic.is_valid_guess("cranes"))

    def test_non_alpha(self):
        self.assertFalse(logic.is_valid_guess("cra1e"))

    def test_uppercase(self):
        self.assertFalse(logic.is_valid_guess("CRANE"))


class IsWinTests(unittest.TestCase):
    def test_win(self):
        self.assertTrue(logic.is_win([logic.CORRECT] * 5))

    def test_no_win_partial(self):
        self.assertFalse(
            logic.is_win([logic.CORRECT] * 4 + [logic.PRESENT]))

    def test_no_win_absent(self):
        self.assertFalse(
            logic.is_win([logic.CORRECT] * 4 + [logic.ABSENT]))


class PickWordTests(unittest.TestCase):
    def test_picks_from_words(self):
        words = ["crane", "slate", "brain"]
        import random
        rng = random.Random(0)
        self.assertIn(logic.pick_word(words, rng), words)

    def test_default_list(self):
        self.assertIn(logic.pick_word(), logic.WORDS)


class ColorizeTests(unittest.TestCase):
    def test_has_reset(self):
        self.assertTrue(logic.colorize("a", logic.CORRECT).endswith("\033[0m"))


if __name__ == "__main__":
    unittest.main()
