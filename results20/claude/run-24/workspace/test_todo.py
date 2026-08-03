"""Tests for todo.py.

Run with:  python3 -m unittest -v
or:        python3 -m pytest  (if installed)
"""

import datetime as dt
import os
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, os.path.dirname(__file__))
import todo  # noqa: E402

# Colors are off under the test runner (not a TTY), which keeps output stable.


class TodoStoreTestCase(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.path = Path(self._tmp.name) / "tasks.json"
        self.store = todo.TodoStore(self.path)

    def seed(self, *tasks):
        self.store.save(list(tasks))
        return self.store.load()

    def t(self, text, **kw):
        return todo.Task(text=text, **kw)


class TestStore(TodoStoreTestCase):
    def test_missing_file_loads_empty(self):
        self.assertEqual(self.store.load(), [])

    def test_round_trip(self):
        task = self.t("write docs", priority="high", project="work", due="2026-08-10", id=1)
        self.store.save([task])
        loaded = self.store.load()
        self.assertEqual(len(loaded), 1)
        got = loaded[0]
        self.assertEqual(got.text, "write docs")
        self.assertEqual(got.priority, "high")
        self.assertEqual(got.project, "work")
        self.assertEqual(got.due, "2026-08-10")
        self.assertEqual(got.id, 1)
        self.assertFalse(got.done)

    def test_corrupt_file_raises_user_error(self):
        self.path.write_text("{ not json !!!")
        with self.assertRaises(todo.TodoError):
            self.store.load()

    def test_save_is_atomic(self):
        self.store.save([self.t("a", id=1), self.t("b", id=2)])
        self.assertFalse(self.path.with_suffix(".json.tmp").exists())
        self.assertEqual(len(self.store.load()), 2)


class TestTaskHelpers(TodoStoreTestCase):
    def test_priority_rank_order(self):
        high, med, low = (
            self.t("h", priority="high"),
            self.t("m", priority="medium"),
            self.t("l", priority="low"),
        )
        self.assertTrue(high.sort_key() < med.sort_key() < low.sort_key())

    def test_overdue_sort_before_priority(self):
        old = self.t("old", due="2000-01-01", priority="low")
        high = self.t("high", priority="high")
        self.assertTrue(old.sort_key() < high.sort_key())

    def test_due_sort_within_priority(self):
        earlier = self.t("a", priority="high", due="2026-08-01")
        later = self.t("b", priority="high", due="2026-08-20")
        self.assertTrue(earlier.sort_key() < later.sort_key())

    def test_unknown_priority_falls_back(self):
        self.assertEqual(self.t("x", priority="banana").priority, "medium")

    def test_default_priority(self):
        self.assertEqual(self.t("x").priority, "medium")


class TestDates(TodoStoreTestCase):
    def test_parse_due_valid(self):
        self.assertEqual(todo.parse_due("2026-12-25"), "2026-12-25")

    def test_parse_due_today_tomorrow(self):
        today = dt.date.today()
        self.assertEqual(todo.parse_due("today"), today.isoformat())
        self.assertEqual(
            todo.parse_due("tomorrow"), (today + dt.timedelta(days=1)).isoformat()
        )

    def test_parse_due_empty(self):
        self.assertIsNone(todo.parse_due(""))
        self.assertIsNone(todo.parse_due(None))

    def test_parse_due_bad(self):
        with self.assertRaises(todo.TodoError):
            todo.parse_due("not-a-date")


class TestIds(TodoStoreTestCase):
    def test_next_id_starts_at_one(self):
        self.assertEqual(todo.next_id([]), 1)

    def test_next_id_increments(self):
        tasks = [self.t("a", id=5), self.t("b", id=9)]
        self.assertEqual(todo.next_id(tasks), 10)

    def test_next_id_handles_sparse(self):
        tasks = [self.t("a", id=3)]
        self.assertEqual(todo.next_id(tasks), 4)

    def test_done_tasks_keep_id(self):
        # Marking done must not reuse someone else's id.
        tasks = [self.t("a", id=1), self.t("b", id=2)]
        tasks[1].done = True
        self.assertEqual(todo.next_id(tasks), 3)


class TestCli(TodoStoreTestCase):
    """End-to-end-ish: run main() against an isolated file."""

    def run_cmd(self, *argv, capture=False):
        # Global -f must come before the subcommand.
        argv = ["-f", str(self.path)] + list(argv)
        if capture:
            import io
            from contextlib import redirect_stdout

            buf = io.StringIO()
            with redirect_stdout(buf):
                code = todo.main(argv)
            return code, buf.getvalue(), self.store.load()
        return todo.main(argv), self.store.load()

    def test_add_and_list_default(self):
        code, tasks = self.run_cmd("add", "ship release", "-p", "high")
        self.assertEqual(code, 0)
        self.assertEqual(len(tasks), 1)
        self.assertEqual(tasks[0].text, "ship release")
        self.assertEqual(tasks[0].priority, "high")
        self.assertEqual(tasks[0].id, 1)

    def test_default_command_lists_open(self):
        self.run_cmd("add", "alpha")
        self.run_cmd("add", "beta")
        self.run_cmd("done", "1")
        code, tasks = self.run_cmd()
        self.assertEqual(code, 0)
        open_tasks = [t for t in tasks if not t.done]
        self.assertEqual([t.text for t in open_tasks], ["beta"])

    def test_done_marks_complete(self):
        self.run_cmd("add", "water plants")
        code, tasks = self.run_cmd("done", "1")
        self.assertEqual(code, 0)
        self.assertTrue(tasks[0].done)

    def test_remove(self):
        self.run_cmd("add", "temporary")
        code, tasks = self.run_cmd("remove", "1", "-y")
        self.assertEqual(code, 0)
        self.assertEqual(tasks, [])

    def test_done_bad_id(self):
        self.run_cmd("add", "only task")
        code, _ = self.run_cmd("done", "99")
        self.assertEqual(code, 1)

    def test_filter_by_project(self):
        self.run_cmd("add", "code", "--project", "work")
        self.run_cmd("add", "gym", "--project", "health")
        code, out, tasks = self.run_cmd("list", "--project", "work", "-a", capture=True)
        self.assertEqual(code, 0)
        self.assertIn("code", out)
        self.assertNotIn("gym", out)
        # Underlying store still has both — filtering happens at view time.
        self.assertEqual(len(tasks), 2)

    def test_filter_by_priority(self):
        self.run_cmd("add", "now", "-p", "high")
        self.run_cmd("add", "later", "-p", "low")
        code, out, tasks = self.run_cmd("list", "-p", "high", "-a", capture=True)
        self.assertEqual(code, 0)
        self.assertIn("now", out)
        self.assertNotIn("later", out)
        self.assertEqual(len(tasks), 2)

    def test_clear_done_keeps_open(self):
        self.run_cmd("add", "open one")
        self.run_cmd("add", "done one")
        self.run_cmd("done", "2")
        code, tasks = self.run_cmd("clear", "--done", "-y")
        self.assertEqual(code, 0)
        self.assertEqual([t.text for t in tasks], ["open one"])
        self.assertFalse(any(t.done for t in tasks))

    def test_invalid_due_reports_error(self):
        code, tasks = self.run_cmd("add", "bad", "--due", "garbage")
        self.assertEqual(code, 1)
        self.assertEqual(tasks, [])

    def test_remove_requires_confirmation(self):
        self.run_cmd("add", "precious")
        # Feed "n" to stdin.
        with __import__("unittest.mock").mock.patch("sys.stdin", _Stdin("n\n")):
            code, tasks = self.run_cmd("remove", "1")
        self.assertEqual(code, 1)
        self.assertEqual(len(tasks), 1)  # not removed


class _Stdin:
    def __init__(self, data):
        import io

        self._buf = io.StringIO(data)

    def readline(self, *a):
        return self._buf.readline(*a)


if __name__ == "__main__":
    unittest.main(verbosity=2)
