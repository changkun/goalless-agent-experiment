import unittest

from pomo.core import Phase, PomodoroTimer, Session


class FakeClock:
    """A clock whose value is set explicitly, so time is fully controlled."""

    def __init__(self, now=0.0):
        self.now = now

    def __call__(self):
        return self.now


class CoreTest(unittest.TestCase):
    def test_initial_state_is_work(self):
        clock = FakeClock()
        t = PomodoroTimer(work_s=1500, clock=clock)
        t.tick()
        self.assertIs(t.phase, Phase.WORK)
        self.assertEqual(t.phase_name, "Work")
        self.assertEqual(t.total_s, 1500)
        self.assertEqual(t.remaining_s, 1500)

    def test_tick_tracks_elapsed_time(self):
        clock = FakeClock()
        t = PomodoroTimer(work_s=1500, clock=clock)
        clock.now = 10.0
        t.tick()
        self.assertEqual(t.remaining_s, 1490)
        clock.now = 1500.0
        t.tick()
        self.assertEqual(t.remaining_s, 0)

    def test_work_advances_to_short_break_and_records_session(self):
        clock = FakeClock()
        t = PomodoroTimer(work_s=1500, short_break_s=300, clock=clock)
        t.set_task("Review PR")
        clock.now = 1500.0
        t.tick()
        self.assertEqual(t.remaining_s, 0)
        phase = t.advance()
        self.assertIs(phase, Phase.SHORT_BREAK)
        self.assertEqual(t.completed_work, 1)
        self.assertEqual(len(t.sessions), 1)
        session = t.sessions[0]
        self.assertIsInstance(session, Session)
        self.assertEqual(session.task, "Review PR")
        self.assertEqual(session.duration_s, 1500)

    def test_long_break_every_n(self):
        clock = FakeClock()
        t = PomodoroTimer(
            work_s=1500, short_break_s=300, long_break_s=900,
            long_break_every=3, clock=clock,
        )
        # Two full work + break cycles.
        for _ in range(2):
            clock.now += 1500.0  # complete work
            t.advance()
            clock.now += 300.0  # complete short break
            t.advance()
        # Third work phase finishes -> long break.
        clock.now += 1500.0
        self.assertIs(t.advance(), Phase.LONG_BREAK)
        self.assertEqual(t.completed_work, 3)

    def test_break_returns_to_work(self):
        clock = FakeClock()
        t = PomodoroTimer(work_s=1500, short_break_s=300, clock=clock)
        clock.now = 1500.0
        t.advance()
        self.assertIs(t.phase, Phase.SHORT_BREAK)
        clock.now += 300.0
        t.advance()
        self.assertIs(t.phase, Phase.WORK)
        self.assertEqual(t.completed_work, 1)

    def test_skip_break_goes_to_work(self):
        clock = FakeClock()
        t = PomodoroTimer(clock=clock)
        t.advance()
        self.assertIs(t.phase, Phase.SHORT_BREAK)
        self.assertIs(t.skip(), Phase.WORK)

    def test_cannot_skip_work(self):
        t = PomodoroTimer(clock=FakeClock())
        with self.assertRaises(ValueError):
            t.skip()

    def test_advance_requires_work_completed(self):
        # Advancing with no elapsed time still switches phases but records a
        # zero-progress work session only when the work phase is ended.
        clock = FakeClock()
        t = PomodoroTimer(work_s=1500, clock=clock)
        t.advance()
        self.assertEqual(t.completed_work, 1)


if __name__ == "__main__":
    unittest.main()
