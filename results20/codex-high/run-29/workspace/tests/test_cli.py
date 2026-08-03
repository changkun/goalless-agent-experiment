import contextlib
import io
import tempfile
import unittest
from pathlib import Path

from habit_tracker.cli import main


class CliTestCase(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.data = str(Path(self.tmp.name) / "habits.json")

    def run_cmd(self, *args):
        return main(["--data", self.data, *args])

    def run_cmd_capture(self, *args):
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            code = self.run_cmd(*args)
        return code, out.getvalue()

    def test_add_done_list_flow(self):
        self.assertEqual(self.run_cmd("add", "Read"), 0)
        self.assertEqual(self.run_cmd("done", "Read"), 0)
        code, out = self.run_cmd_capture("list")
        self.assertEqual(code, 0)
        self.assertIn("Read", out)
        self.assertIn("streak 1", out)

    def test_add_duplicate_returns_error(self):
        self.assertEqual(self.run_cmd("add", "Run"), 0)
        self.assertEqual(self.run_cmd("add", "Run"), 1)

    def test_done_missing_habit_returns_error(self):
        self.assertEqual(self.run_cmd("done", "Ghost"), 1)

    def test_undo_flow(self):
        self.assertEqual(self.run_cmd("add", "Med"), 0)
        self.assertEqual(self.run_cmd("done", "Med"), 0)
        self.assertEqual(self.run_cmd("undo", "Med"), 0)


if __name__ == "__main__":
    unittest.main()
