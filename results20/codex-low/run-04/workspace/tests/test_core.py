import unittest

from focus_timer.core import Cycle, frame_at, PHASE_BREAK, PHASE_FOCUS


class CycleTests(unittest.TestCase):
    def test_from_minutes(self):
        c = Cycle.from_minutes(25, 5)
        self.assertEqual(c.focus_seconds, 1500)
        self.assertEqual(c.break_seconds, 300)

    def test_invalid_total_raises(self):
        with self.assertRaises(ValueError):
            frame_at(0, Cycle(0, 0))


class FrameTests(unittest.TestCase):
    def setUp(self):
        self.cycle = Cycle(25, 5)  # 30s total in "seconds" for quick math

    def test_start_is_focus(self):
        f = frame_at(0, self.cycle)
        self.assertEqual(f.phase, PHASE_FOCUS)
        self.assertEqual(f.remaining_seconds, 25)
        self.assertEqual(f.completed_focus_sessions, 0)

    def test_break_phase(self):
        f = frame_at(25, self.cycle)
        self.assertEqual(f.phase, PHASE_BREAK)
        self.assertEqual(f.remaining_seconds, 5)
        self.assertEqual(f.completed_focus_sessions, 1)

    def test_second_cycle(self):
        # 30s start of the second full cycle -> focus again
        f = frame_at(30, self.cycle)
        self.assertEqual(f.phase, PHASE_FOCUS)
        self.assertEqual(f.remaining_seconds, 25)
        self.assertEqual(f.completed_focus_sessions, 1)

    def test_second_break_sessions(self):
        f = frame_at(55, self.cycle)  # 25 focus + 5 break + 25 focus
        self.assertEqual(f.phase, PHASE_BREAK)
        self.assertEqual(f.completed_focus_sessions, 2)

    def test_negative_elapsed(self):
        f = frame_at(-50, self.cycle)
        self.assertEqual(f.phase, PHASE_FOCUS)
        self.assertEqual(f.remaining_seconds, 25)

    def test_percent_monotonic(self):
        f1 = frame_at(0, self.cycle)
        f2 = frame_at(12, self.cycle)
        self.assertLess(f1.percent, f2.percent)
        self.assertAlmostEqual(frame_at(24, self.cycle).percent, 24 / 25)
        self.assertEqual(frame_at(25, self.cycle).percent, 0.0)  # break just started


if __name__ == "__main__":
    unittest.main()
