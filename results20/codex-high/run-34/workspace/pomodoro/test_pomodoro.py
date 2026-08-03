import json
import unittest
from pathlib import Path
from unittest import mock

import pomodoro


class PomodoroTest(unittest.TestCase):
    def setUp(self):
        self.tmp = Path("/tmp/dropdata3")
        self.tmp.mkdir(parents=True, exist_ok=True)
        p = mock.patch.object(pomodoro, "log_path",
                              return_value=self.tmp / "sessions.json")
        p.start()
        self.addCleanup(p.stop)

    def _seed(self, rows):
        (self.tmp / "sessions.json").write_text(json.dumps(rows))

    def test_append_and_stats(self):
        pomodoro.append_session(1500, "focus", True)
        pomodoro.append_session(300, "break", True)
        with mock.patch("builtins.print") as pr:
            pomodoro.stats(days=7, today_only=False)
        out = " ".join(str(a) for a in pr.call_args_list)
        self.assertIn("25m", out)

    def test_fmt_duration(self):
        self.assertEqual(pomodoro.fmt_duration(59), "59s")
        self.assertEqual(pomodoro.fmt_duration(1500), "25m")
        self.assertEqual(pomodoro.fmt_duration(3661), "1h01m")

    def test_bar(self):
        self.assertIn("#", pomodoro.bar(1.0))
        self.assertIn("-", pomodoro.bar(0.0))

    def test_pomodoro_flow(self):
        with mock.patch.object(pomodoro, "run_timer", return_value=True) as rt:
            with mock.patch.object(pomodoro, "append_session") as ap:
                pomodoro.pomodoro(3, {"focus": 60, "short": 30, "long": 90, "cycles": 4})
        self.assertEqual(len(rt.call_args_list), 5)  # 3 focus + 2 breaks
        # every block appended
        self.assertEqual(len(ap.call_args_list), 5)


if __name__ == "__main__":
    unittest.main(verbosity=2)
