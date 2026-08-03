import unittest

from mnemo.sm2 import (
    MIN_EASE,
    QUALITY_EASY,
    QUALITY_GOOD,
    QUALITY_HARD,
    CardState,
    schedule,
)


class ScheduleTest(unittest.TestCase):
    def test_quality_out_of_range(self):
        with self.assertRaises(ValueError):
            schedule(CardState(), 6, 0)

    def test_new_card_good_gets_one_day_interval(self):
        st = schedule(CardState(), QUALITY_GOOD, 100)
        self.assertEqual(st.interval, 1)
        self.assertEqual(st.reps, 1)
        self.assertEqual(st.lapses, 0)

    def test_failure_lapses_card(self):
        st = schedule(CardState(), 0, 100)
        self.assertEqual(st.interval, 1)
        self.assertEqual(st.reps, 0)
        self.assertEqual(st.lapses, 1)
        # ease drops
        self.assertAlmostEqual(st.ease, 2.5 - 0.2)

    def test_interval_growth_sequence(self):
        # Review "good" every day; intervals should follow 1, 6, then grow.
        st = CardState()
        st = schedule(st, QUALITY_GOOD, 1)   # -> 1
        self.assertEqual(st.interval, 1)
        st = schedule(st, QUALITY_GOOD, 1)   # -> 6
        self.assertEqual(st.interval, 6)
        st = schedule(st, QUALITY_GOOD, 1)   # -> round(6*2.5)=15
        self.assertEqual(st.interval, 15)

    def test_ease_floor_never_below_min(self):
        st = CardState(ease=MIN_EASE)
        st = schedule(st, 0, 100)
        self.assertGreaterEqual(st.ease, MIN_EASE)

    def test_hard_pass_shaves_ease(self):
        st = schedule(CardState(), QUALITY_HARD, 100)
        self.assertAlmostEqual(st.ease, 2.5 - 0.15)

    def test_lapse_reduces_future_interval_growth(self):
        # A lapsed card keeps its (reduced) ease from shrinking intervals.
        base = schedule(CardState(), QUALITY_GOOD, 100)
        lapsed = schedule(CardState(interval=base.interval,
                                    ease=base.ease, reps=3), 0, 101)
        self.assertEqual(lapsed.interval, 1)
        self.assertLess(lapsed.ease, base.ease)

    def test_easy_grows_interval_faster(self):
        good = schedule(CardState(), QUALITY_GOOD, 100)
        easy = schedule(CardState(), QUALITY_EASY, 100)
        self.assertGreater(easy.interval, good.interval)


if __name__ == "__main__":
    unittest.main()
