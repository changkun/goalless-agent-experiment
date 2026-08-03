"""Tests for the terminal todo CLI."""
import sys
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

from todo_app.cli import main


class CliTest(unittest.TestCase):
    def setUp(self):
        self.tmp = TemporaryDirectory()
        self.task_file = str(Path(self.tmp.name) / "tasks.json")

    def tearDown(self):
        self.tmp.cleanup()

    def run_cli(self, *args):
        out = []
        err = []
        def fake_out(line=""):
            out.append(line)
        def fake_err(line=""):
            err.append(line)
        with patch("sys.stdout.write", side_effect=fake_out), \
             patch("sys.stderr.write", side_effect=fake_err):
            code = main(["--file", self.task_file, *args])
        return code, "".join(out), "".join(err)

    def test_add_and_list(self):
        code, out, _ = self.run_cli("add", "Buy milk")
        self.assertEqual(code, 0)
        self.assertIn("Buy milk", out)
        _, listing, _ = self.run_cli("list")
        self.assertIn("Buy milk", listing)

    def test_done_toggle(self):
        self.run_cli("add", "task one")
        self.run_cli("add", "task two")
        self.run_cli("done", "1")
        _, open_list, _ = self.run_cli("list", "--open")
        self.assertNotIn("task one", open_list)
        self.assertIn("task two", open_list)
        _, done_list, _ = self.run_cli("list", "--done")
        self.assertIn("task one", done_list)

    def test_invalid_command_exits_nonzero(self):
        code, _, err = self.run_cli("done", "999")
        self.assertEqual(code, 1)
        self.assertIn("no task", err)


if __name__ == "__main__":
    unittest.main()
