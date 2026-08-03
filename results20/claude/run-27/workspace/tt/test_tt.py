"""Tests for tt. Run with: python3 -m pytest test_tt.py (or unittest)."""

import json
import os
import subprocess
import sys
import tempfile
import time
import unittest
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import tt  # noqa: E402

TT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "tt.py")


def run(*args, env_extra=None, subcommand=None):
    """Run the bundled launcher with TT_STORE pointed at a temp file."""
    env = dict(os.environ)
    if env_extra:
        env.update(env_extra)
    return subprocess.run(
        [sys.executable, TT] + list(args),
        capture_output=True, text=True, env=env,
    )


class FunctionalTests(unittest.TestCase):
    def setUp(self):
        self.dir = tempfile.TemporaryDirectory()
        self.store = os.path.join(self.dir.name, "tasks.json")
        self.env = {"TT_STORE": self.store}

    def tearDown(self):
        self.dir.cleanup()

    def test_add_and_list_roundtrip(self):
        r = run("add", "buy milk", env_extra=self.env)
        self.assertEqual(r.returncode, 0)
        r = run("list", env_extra=self.env)
        self.assertIn("buy milk", r.stdout)
        self.assertIn("1 open", r.stdout)

    def test_done_undo_clear(self):
        run("add", "a", env_extra=self.env)
        run("add", "b", env_extra=self.env)
        run("done", "1", env_extra=self.env)
        # done shows the checkmark
        r = run("list", env_extra=self.env)
        self.assertIn("1 open", r.stdout)
        # undo reopens it
        run("undo", "1", env_extra=self.env)
        r = run("list", env_extra=self.env)
        self.assertIn("2 open", r.stdout)
        # clear removes only done tasks
        run("done", "1", env_extra=self.env)
        run("clear", env_extra=self.env)
        r = run("list", env_extra=self.env)
        self.assertNotIn("  a", r.stdout)   # task "a" is gone...
        self.assertIn("  b", r.stdout)      # ...but "b" remains

    def test_delete(self):
        run("add", "x", env_extra=self.env)
        run("add", "y", env_extra=self.env)
        r = run("delete", "1", env_extra=self.env)
        self.assertEqual(r.returncode, 0)
        r = run("list", env_extra=self.env)
        self.assertNotIn("x", r.stdout)
        self.assertIn("y", r.stdout)

    def test_store_persists_to_disk_as_json(self):
        run("add", "hello", env_extra=self.env)
        data = json.loads(Path(self.store).read_text())
        self.assertEqual(data[0]["text"], "hello")
        self.assertFalse(data[0]["done"])

    def test_unknown_task_errors_cleanly(self):
        r = run("done", "999", env_extra=self.env)
        self.assertEqual(r.returncode, 1)
        self.assertIn("no task", r.stderr)

    def test_no_arguments_prints_usage(self):
        r = run(env_extra=self.env)
        self.assertEqual(r.returncode, 2)
        self.assertIn("usage", r.stdout)

    def test_version(self):
        r = run("version", env_extra=self.env)
        self.assertEqual(r.returncode, 0)
        self.assertEqual(r.stdout.strip(), f"tt {tt.VERSION}")

    def test_piped_output_is_plain(self):
        """In a pipe there is no TTY, so no ANSI escape codes."""
        run("add", "colour", env_extra=self.env)
        r = run("list", env_extra=self.env)
        self.assertNotIn("\x1b[", r.stdout)


class ModelTests(unittest.TestCase):
    def test_ids_auto_increment_after_deleted_task(self):
        path = Path(tempfile.mkdtemp()) / "t.json"
        path.parent.mkdir(exist_ok=True)
        path.write_text(json.dumps([
            {"id": 3, "text": "last"},
            {"id": 2, "text": "mid"},
            {"id": 1, "text": "first"},
        ]))
        tasks = tt._load(path)
        # next id should skip nothing problematic: 4
        self.assertEqual([t.id for t in tasks], [3, 2, 1])
        self.assertEqual(tt._next_id(tasks), 4)

    def test_corrupt_store_reports_error(self):
        path = Path(tempfile.mkdtemp()) / "c.json"
        path.write_text("{ not json")
        with self.assertRaises(tt.StoreError):
            tt._load(path)


if __name__ == "__main__":
    unittest.main()
