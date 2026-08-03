import tempfile
import unittest
from pathlib import Path

from todo import (
    Store,
    Task,
    add_task,
    list_tasks,
    mark_done,
    record_pomodoro,
    remove_task,
)


class StoreTestCase(unittest.TestCase):
    def setUp(self):
        self.dir = tempfile.TemporaryDirectory()
        self.store = Store(Path(self.dir.name) / "tasks.json")

    def tearDown(self):
        self.dir.cleanup()

    def test_add_and_assigns_incrementing_ids(self):
        a = add_task(self.store, "first", "high")
        b = add_task(self.store, "second", "low")
        self.assertEqual((a.id, b.id), (1, 2))

    def test_add_priorities(self):
        add_task(self.store, "t", "high")
        task = list_tasks(self.store)[0]
        self.assertEqual(task.priority, "high")

    def test_mark_done_sets_completed_at(self):
        a = add_task(self.store, "go")
        mark_done(self.store, a.id)
        task = list_tasks(self.store)[0]
        self.assertTrue(task.done)
        self.assertIsNotNone(task.completed_at)

    def test_remove_task(self):
        a = add_task(self.store, "go")
        remove_task(self.store, a.id)
        self.assertEqual(list_tasks(self.store), [])

    def test_record_pomodoro_increments(self):
        a = add_task(self.store, "go")
        record_pomodoro(self.store, a.id)
        task = list_tasks(self.store)[0]
        self.assertEqual(task.pomodoros, 1)

    def test_missing_task_raises(self):
        with self.assertRaises(KeyError):
            mark_done(self.store, 999)

    def test_incomplete_filter(self):
        a = add_task(self.store, "open task")
        b = add_task(self.store, "closed task")
        mark_done(self.store, b.id)
        open_tasks = list_tasks(self.store, show_done=False)
        self.assertEqual([t.id for t in open_tasks], [a.id])

    def test_roundtrip_persistence(self):
        add_task(self.store, "one")
        reloaded = Store(self.store.path)
        self.assertEqual([t.description for t in reloaded.load()], ["one"])

    def test_load_empty_missing_file(self):
        self.assertEqual(self.store.load(), [])


if __name__ == "__main__":
    unittest.main()
