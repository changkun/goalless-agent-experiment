"""Tests for the terminal todo store."""
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from todo_app.store import Store, TodoError, sort_key, format_task


class StoreTest(unittest.TestCase):
    def setUp(self):
        self.tmp = TemporaryDirectory()
        self.path = Path(self.tmp.name) / "tasks.json"

    def tearDown(self):
        self.tmp.cleanup()

    def make(self):
        return Store(self.path)

    def test_add_and_load(self):
        store = self.make()
        task = store.add("Buy milk", priority="high", due="2026-08-10")
        self.assertEqual(task["title"], "Buy milk")
        self.assertEqual(task["priority"], "high")
        self.assertEqual(task["due"], "2026-08-10")
        self.assertFalse(task["done"])
        self.assertEqual(store.list_all(), [task])

    def test_ids_increment(self):
        store = self.make()
        first = store.add("one")
        second = store.add("two")
        self.assertEqual(first["id"], 1)
        self.assertEqual(second["id"], 2)

    def test_priority_validated(self):
        store = self.make()
        with self.assertRaises(TodoError):
            store.add("x", priority="urgent")

    def test_priority_defaults_to_normal(self):
        store = self.make()
        task = store.add("x")
        self.assertEqual(task["priority"], "normal")

    def test_due_date_validated(self):
        store = self.make()
        with self.assertRaises(TodoError):
            store.add("x", due="10/08/2026")
        with self.assertRaises(TodoError):
            store.add("x", due="garbage")

    def test_empty_title_rejected(self):
        store = self.make()
        with self.assertRaises(TodoError):
            store.add("   ")

    def test_title_is_stripped(self):
        store = self.make()
        self.assertEqual(store.add("  hi  ")["title"], "hi")

    def test_done_and_open_filters(self):
        store = self.make()
        store.add("a")
        store.add("b")
        store.set_done(2, True)
        self.assertEqual([t["id"] for t in store.list_all(filter_done=True)], [2])
        self.assertEqual([t["id"] for t in store.list_all(filter_done=False)], [1])

    def test_update(self):
        store = self.make()
        task = store.add("old", due="2026-01-01")
        updated = store.update(task["id"], title="new", priority="low")
        self.assertEqual(updated["title"], "new")
        self.assertEqual(updated["priority"], "low")
        self.assertEqual(updated["due"], "2026-01-01")

    def test_clear_due_date(self):
        store = self.make()
        task = store.add("x", due="2026-01-01")
        store.update(task["id"], due="")
        self.assertIsNone(store.list_all()[0]["due"])

    def test_delete(self):
        store = self.make()
        store.add("a")
        task = store.add("b")
        store.delete(task["id"])
        self.assertEqual([t["title"] for t in store.list_all()], ["a"])

    def test_clear_done(self):
        store = self.make()
        store.add("a")
        store.add("b")
        store.set_done(1, True)
        removed = store.clear_done()
        self.assertEqual(removed, 1)
        self.assertEqual([t["title"] for t in store.list_all()], ["b"])

    def test_missing_task_raises(self):
        store = self.make()
        with self.assertRaises(TodoError):
            store.set_done(99, True)

    def test_persistence_across_instances(self):
        store = self.make()
        store.add("persist me")
        other = Store(self.path)
        self.assertEqual(other.list_all()[0]["title"], "persist me")

    def test_corrupt_file_raises(self):
        self.path.write_text("not json{", encoding="utf-8")
        store = self.make()
        with self.assertRaises(TodoError):
            store.list_all()


class SortAndFormatTest(unittest.TestCase):
    def test_sort_orders_open_before_done(self):
        done = {"id": 1, "done": True, "priority": "high", "due": "2026-01-01"}
        open_ = {"id": 2, "done": False, "priority": "low", "due": "2026-01-01"}
        self.assertLess(sort_key(open_), sort_key(done))

    def test_sort_priority(self):
        high = {"id": 1, "done": False, "priority": "high", "due": None}
        low = {"id": 2, "done": False, "priority": "low", "due": None}
        self.assertLess(sort_key(high), sort_key(low))

    def test_format(self):
        task = {"id": 3, "title": "write", "done": False, "priority": "high", "due": None}
        self.assertEqual(format_task(task), "#3 [ ] write (high)")


if __name__ == "__main__":
    unittest.main()
