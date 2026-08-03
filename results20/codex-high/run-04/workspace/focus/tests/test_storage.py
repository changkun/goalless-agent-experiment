import tempfile
import unittest
from pathlib import Path

from focus.storage import STATUS_OPEN, TaskStore


class TaskStoreTest(unittest.TestCase):
    def setUp(self):
        self.dir = tempfile.TemporaryDirectory()
        self.path = Path(self.dir.name) / "tasks.json"

    def tearDown(self):
        self.dir.cleanup()

    def test_add_and_list(self):
        store = TaskStore(self.path)
        a = store.add("Write post", ["writing", "work"])
        b = store.add("Read book", [])
        self.assertEqual(a.id, 1)
        self.assertEqual(b.id, 2)
        self.assertEqual([t.title for t in store.open_tasks()], ["Write post", "Read book"])
        self.assertEqual(a.tags, ["work", "writing"])

    def test_persistence(self):
        store = TaskStore(self.path)
        store.add("Alpha", [])
        store.save()

        reloaded = TaskStore(self.path)
        self.assertEqual(len(reloaded.tasks), 1)
        self.assertEqual(reloaded.tasks[0].title, "Alpha")
        # next id continues after reload
        reloaded.add("Beta", [])
        reloaded.save()
        self.assertEqual([t.id for t in TaskStore(self.path).tasks], [1, 2])

    def test_done_reopen(self):
        store = TaskStore(self.path)
        t = store.add("Task", [])
        self.assertTrue(store.close(t.id))
        self.assertFalse(store.close(t.id))  # already closed
        self.assertTrue(store.reopen(t.id))
        self.assertFalse(store.reopen(t.id))  # already open

    def test_remove_and_clear(self):
        store = TaskStore(self.path)
        store.add("one", [])
        store.add("two", [])
        store.close(1)
        self.assertTrue(store.remove(99) is False)
        self.assertEqual(store.clear_closed(), 1)
        self.assertEqual([t.id for t in store.tasks], [2])

    def test_pomodoro_counter(self):
        store = TaskStore(self.path)
        t = store.add("Task", [])
        self.assertTrue(store.add_pomodoro(t.id))
        self.assertEqual(t.pomodoros, 1)
        self.assertFalse(store.add_pomodoro(999))


if __name__ == "__main__":
    unittest.main()
