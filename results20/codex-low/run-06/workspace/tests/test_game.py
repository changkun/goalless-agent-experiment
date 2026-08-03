import unittest

from wordle_cli.game import Game, Feedback, MAX_ATTEMPTS


class ScoreTest(unittest.TestCase):
    def test_all_green(self):
        self.assertEqual(
            Game.score("crane", "crane"),
            [Feedback.GREEN] * 5,
        )

    def test_all_gray(self):
        self.assertEqual(
            Game.score("zzzzz", "crane"),
            [Feedback.GRAY] * 5,
        )

    def test_misplaced_yellow(self):
        self.assertEqual(
            Game.score("aecrn", "crane"),
            [Feedback.YELLOW] * 5,
        )

    def test_no_duplicate_yellow_overuse(self):
        # guess "creep": secret "crane" has only one 'e', so the two guessed
        # 'e's must not both count as present.
        result = Game.score("creep", "crane")
        # c and r are right; first 'e' is misplaced; second 'e' and 'p' absent.
        self.assertEqual(result, [
            Feedback.GREEN,
            Feedback.GREEN,
            Feedback.YELLOW,
            Feedback.GRAY,
            Feedback.GRAY,
        ])

    def test_case_insensitive(self):
        self.assertEqual(
            Game.score("CRANE", "crane"),
            [Feedback.GREEN] * 5,
        )


class GameTest(unittest.TestCase):
    def test_win_in_one(self):
        g = Game(secret="crane")
        fb = g.submit("crane")
        self.assertTrue(g.is_won)
        self.assertTrue(g.is_over)
        self.assertEqual(fb, [Feedback.GREEN] * 5)

    def test_invalid_length_rejected(self):
        g = Game(secret="crane")
        with self.assertRaises(ValueError):
            g.submit("cr")
        self.assertEqual(len(g.guesses), 0)

    def test_non_alpha_rejected(self):
        g = Game(secret="crane")
        with self.assertRaises(ValueError):
            g.submit("cra1e")
        self.assertEqual(len(g.guesses), 0)

    def test_over_rejected(self):
        g = Game(secret="crane", max_attempts=1)
        g.submit("crane")
        with self.assertRaises(ValueError):
            g.submit("crane")

    def test_out_of_attempts(self):
        g = Game(secret="crane", max_attempts=1)
        g.submit("zzzzz")
        self.assertFalse(g.is_won)
        self.assertTrue(g.is_over)


if __name__ == "__main__":
    unittest.main()
