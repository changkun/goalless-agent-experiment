import json
import unittest
from pathlib import Path
import tempfile

from todo.store import TaskStore


class TestTaskStore(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.store = TaskStore(Path(self.tmp.name) / "todo.json")

    def tearDown(self):
        self.tmp.cleanup()

    def test_add_and_list(self):
        self.store.add("buy milk")
        self.store.add("walk dog")
        self.assertEqual([t.text for t in self.store.list()], ["buy milk", "walk dog"])

    def test_done(self):
        task = self.store.add("buy milk")
        self.store.done(task.id)
        self.assertEqual(self.store.list(), [])
        self.assertTrue(self.store.list(show_all=True)[0].done)

    def test_done_missing(self):
        self.assertIsNone(self.store.done(42))

    def test_remove(self):
        task = self.store.add("buy milk")
        self.assertTrue(self.store.remove(task.id))
        self.assertEqual(self.store.list(), [])

    def test_remove_missing(self):
        self.assertFalse(self.store.remove(42))

    def test_persistence(self):
        task = self.store.add("buy milk")
        self.store.done(task.id)

        data = json.loads(self.store.path.read_text())
        self.assertEqual(data["next_id"], 2)
        self.assertEqual(data["tasks"][0]["text"], "buy milk")
        self.assertTrue(data["tasks"][0]["done"])

        store2 = TaskStore(self.store.path)
        self.assertEqual(len(store2.list(show_all=True)), 1)


if __name__ == "__main__":
    unittest.main()
