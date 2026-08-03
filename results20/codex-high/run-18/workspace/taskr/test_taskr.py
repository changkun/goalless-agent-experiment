import os
import subprocess
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.dirname(__file__))
import taskr


def run_cli(*argv):
    return subprocess.run(
        [sys.executable, os.path.join(os.path.dirname(__file__), "taskr.py"), *argv],
        capture_output=True,
        text=True,
    )


class TaskrTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.NamedTemporaryFile(delete=False)
        self.tmp.close()
        self.path = self.tmp.name

    def tearDown(self):
        os.unlink(self.path)

    def test_add_and_list(self):
        res = run_cli("--file", self.path, "add", "buy", "milk")
        self.assertEqual(res.returncode, 0)
        tasks = taskr.load(self.path)
        self.assertEqual(len(tasks), 1)
        self.assertEqual(tasks[0]["description"], "buy milk")
        self.assertEqual(tasks[0]["status"], "todo")
        self.assertIn("id", tasks[0])

    def test_update_status_and_description(self):
        run_cli("--file", self.path, "add", "write", "report")
        task_id = taskr.load(self.path)[0]["id"]
        res = run_cli("--file", self.path, "update", task_id, "--status", "done")
        self.assertEqual(res.returncode, 0)
        self.assertEqual(taskr.load(self.path)[0]["status"], "done")
        res = run_cli("--file", self.path, "update", task_id, "--description", "final", "draft")
        self.assertEqual(res.returncode, 0)
        self.assertEqual(taskr.load(self.path)[0]["description"], "final draft")

    def test_delete(self):
        run_cli("--file", self.path, "add", "temp")
        task_id = taskr.load(self.path)[0]["id"]
        res = run_cli("--file", self.path, "delete", task_id)
        self.assertEqual(res.returncode, 0)
        self.assertEqual(taskr.load(self.path), [])

    def test_filter_by_status(self):
        run_cli("--file", self.path, "add", "a")
        task_id = taskr.load(self.path)[0]["id"]
        run_cli("--file", self.path, "update", task_id, "--status", "done")
        run_cli("--file", self.path, "add", "b")
        res = run_cli("--file", self.path, "list", "--status", "todo")
        self.assertTrue(any(line.strip().endswith("b") for line in res.stdout.splitlines()))

    def test_missing_task_errors(self):
        res = run_cli("--file", self.path, "update", "nope")
        self.assertEqual(res.returncode, 1)
        self.assertIn("no task", res.stderr)

    def test_invalid_status_errors(self):
        res = run_cli("--file", self.path, "list", "--status", "bogus")
        self.assertEqual(res.returncode, 2)


if __name__ == "__main__":
    unittest.main()
