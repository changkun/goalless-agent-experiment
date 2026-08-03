import unittest

from pomodoro.core import (
    SessionType,
    Timer,
    format_time,
)


class TimerTests(unittest.TestCase):
    def test_initial_state(self):
        timer = Timer(focus_minutes=1, short_break_minutes=1, long_break_minutes=1)
        self.assertIs(timer.session_type, SessionType.FOCUS)
        self.assertEqual(timer.remaining, 60)
        self.assertEqual(timer.elapsed, 0)
        self.assertEqual(timer.completed_sessions, 0)
        self.assertEqual(timer.focus_count, 0)

    def test_tick_does_not_finish_before_end(self):
        timer = Timer(focus_minutes=1)
        self.assertIsNone(timer.tick(59))
        self.assertIs(timer.session_type, SessionType.FOCUS)
        self.assertEqual(timer.remaining, 1)

    def test_focus_transitions_to_short_break(self):
        timer = Timer(focus_minutes=1, short_break_minutes=2)
        completed = timer.tick(60)
        self.assertIsNotNone(completed)
        self.assertIs(completed.type, SessionType.FOCUS)
        self.assertIs(timer.session_type, SessionType.SHORT_BREAK)
        self.assertEqual(timer.remaining, 120)
        self.assertEqual(timer.completed_sessions, 1)

    def test_cycle_reaches_long_break(self):
        timer = Timer(focus_minutes=1, short_break_minutes=1, long_break_minutes=1)
        for _ in range(3):
            timer.tick(60)  # focus
            timer.tick(60)  # short break
        timer.tick(60)  # 4th focus -> long break
        self.assertEqual(timer.focus_count, 4)
        self.assertIs(timer.session_type, SessionType.LONG_BREAK)
        self.assertEqual(timer.completed_sessions, 4)

    def test_long_break_returns_to_focus(self):
        timer = Timer(focus_minutes=1, short_break_minutes=1, long_break_minutes=1)
        for _ in range(3):
            timer.tick(60)
            timer.tick(60)
        timer.tick(60)  # 4th focus -> long break
        timer.tick(60)  # complete the long break -> focus
        self.assertIs(timer.session_type, SessionType.FOCUS)
        self.assertEqual(timer.focus_count, 4)

    def test_focus_can_cross_multiple_sessions_in_one_tick(self):
        timer = Timer(focus_minutes=1, short_break_minutes=1, long_break_minutes=1)
        timer.tick(120)  # finish focus (60) + finish short break (60)
        self.assertIs(timer.session_type, SessionType.FOCUS)
        self.assertEqual(timer.completed_sessions, 1)
        self.assertEqual(timer.remaining, 60)

    def test_invalid_durations(self):
        with self.assertRaises(ValueError):
            Timer(focus_minutes=0)
        with self.assertRaises(ValueError):
            Timer(sessions_per_cycle=0)

    def test_invalid_tick(self):
        timer = Timer(focus_minutes=1)
        with self.assertRaises(ValueError):
            timer.tick(0)


class FormatTimeTests(unittest.TestCase):
    def test_format_time(self):
        self.assertEqual(format_time(0), "00:00")
        self.assertEqual(format_time(59), "00:59")
        self.assertEqual(format_time(60), "01:00")
        self.assertEqual(format_time(7540), "2:05:40")
        self.assertEqual(format_time(-5), "00:00")


if __name__ == "__main__":
    unittest.main()
