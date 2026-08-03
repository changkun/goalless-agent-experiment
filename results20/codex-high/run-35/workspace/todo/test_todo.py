import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPT = Path(__file__).parent / "todo.py"


class TodoTests(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.file = Path(self._tmp.name) / "tasks.md"

    def run_todo(self, *args):
        env = dict(os.environ)
        return subprocess.run(
            [sys.executable, str(SCRIPT), "--file", str(self.file), *args],
            capture_output=True, text=True, env=env,
        )

    def test_add_list_done_edit_rm(self):
        r = self.run_todo("add", "Buy groceries", "--priority", "high",
                          "--tag", "errands", "--due", "2026-08-05")
        self.assertEqual(r.returncode, 0, r.stderr)

        r = self.run_todo("list")
        self.assertEqual(r.returncode, 0)
        self.assertIn("Buy groceries", r.stdout)
        self.assertIn("(high)", r.stdout)
        self.assertIn("[errands]", r.stdout)
        self.assertIn("(due 2026-08-05)", r.stdout)

        self.assertEqual(self.run_todo("done", "1").returncode, 0)
        r = self.run_todo("list")
        self.assertNotIn("Buy groceries", r.stdout)  # hidden once done
        r = self.run_todo("list", "--all")
        self.assertIn("[x]", r.stdout)

        self.assertEqual(self.run_todo("edit", "1", "Buy", "cake").returncode, 0)
        r = self.run_todo("list", "--all")
        self.assertIn("Buy cake", r.stdout)

        self.assertEqual(self.run_todo("rm", "1").returncode, 0)
        r = self.run_todo("list", "--all")
        self.assertIn("No tasks", r.stdout)

    def test_persistence_round_trip(self):
        r = self.run_todo("add", "hello", "--tag", "a", "--tag", "b")
        self.assertEqual(r.returncode, 0)
        text = self.file.read_text()
        self.assertTrue(text.startswith("- [ ] (medium)"))
        self.assertIn("[a]", text)
        self.assertIn("[b]", text)

    def test_bad_index(self):
        r = self.run_todo("rm", "9")
        self.assertNotEqual(r.returncode, 0)
        self.assertIn("index out of range", r.stderr)


if __name__ == "__main__":
    unittest.main()
