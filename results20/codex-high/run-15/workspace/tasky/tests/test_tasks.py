import json
import tempfile
import unittest
from pathlib import Path

from tasky.tasks import Task, TaskStore


class TaskStoreTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.path = Path(self.tmp.name) / "tasks.json"
        self.store = TaskStore(self.path)

    def tearDown(self):
        self.tmp.cleanup()

    def test_add_and_get(self):
        task = self.store.add("buy milk")
        self.assertTrue(task.id)
        self.assertEqual("buy milk", task.title)
        self.assertFalse(task.done)
        fetched = self.store.get(task.id)
        self.assertEqual(task, fetched)

    def test_all_sorted_done_last(self):
        a = self.store.add("first")
        b = self.store.add("second")
        self.store.set_done(b.id, True)
        ids = [t.id for t in self.store.all()]
        self.assertEqual([a.id, b.id], ids)

    def test_round_trip_via_disk(self):
        self.store.add("persist me")
        reloaded = TaskStore(self.path)
        self.assertEqual(1, len(reloaded.all()))
        self.assertEqual("persist me", reloaded.all()[0].title)

    def test_set_done_undo(self):
        task = self.store.add("do it")
        self.store.set_done(task.id, True)
        self.assertTrue(self.store.get(task.id).done)
        self.store.set_done(task.id, False)
        self.assertFalse(self.store.get(task.id).done)

    def test_set_done_unknown_returns_none(self):
        self.assertIsNone(self.store.set_done("nope", True))

    def test_remove(self):
        task = self.store.add("gone soon")
        self.assertTrue(self.store.remove(task.id))
        self.assertFalse(self.store.remove(task.id))
        self.assertIsNone(self.store.get(task.id))

    def test_clear(self):
        self.store.add("a")
        self.store.add("b")
        self.store.clear()
        self.assertEqual(0, len(self.store.all()))

    def test_corrupt_file_recovers_empty(self):
        self.path.write_text("{not valid json", encoding="utf-8")
        store = TaskStore(self.path)
        self.assertEqual(0, len(store.all()))

    def test_file_nested_dirs_created(self):
        nested = self.path.parent / "deep" / "sub" / "tasks.json"
        store = TaskStore(nested)
        task = store.add("deep task")
        self.assertTrue(nested.exists())
        self.assertIsNotNone(store.get(task.id))


class TaskTest(unittest.TestCase):
    def test_round_trip_dict(self):
        task = Task(id="abc", title="hi", done=True, created_at=1.0)
        restored = Task.from_dict(task.to_dict())
        self.assertEqual(task, restored)
        self.assertEqual(json.dumps({"id": "abc", "title": "hi", "done": True, "created_at": 1.0}),
                         json.dumps(task.to_dict()))


if __name__ == "__main__":
    unittest.main()
