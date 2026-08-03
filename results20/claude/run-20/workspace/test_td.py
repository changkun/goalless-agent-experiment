"""Unit tests for td.py (uses the standard library unittest)."""

import os
import tempfile
import unittest

import td


class TdTestCase(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.TemporaryDirectory()
        self.store_path = os.path.join(self.tmpdir.name, "store.json")
        self.store = td.Store(self.store_path).load()

    def tearDown(self):
        self.tmpdir.cleanup()

    def add(self, text, tags=None):
        return td.cmd_add(self.store, text, tags or [], verbose=False)

    def test_add_and_list(self):
        self.add("write code")
        self.add("check email", tags=["boring"])
        self.assertEqual(self.store.tasks[0].text, "write code")
        self.assertEqual(self.store.tasks[0].id, 1)
        self.assertEqual(self.store.tasks[1].tags, ["boring"])
        # ids are unique, not positional
        self.assertEqual([t.id for t in self.store.tasks], [1, 2])

    def test_persistence_roundtrip(self):
        self.add("persist me")
        reloaded = td.Store(self.store_path).load()
        self.assertEqual(len(reloaded.tasks), 1)
        self.assertEqual(reloaded.tasks[0].text, "persist me")
        self.assertEqual(reloaded._next_id, 2)  # next id survives reload

    def test_done_and_undone(self):
        self.add("a")
        td.cmd_done(self.store, 1)
        self.assertTrue(self.store.tasks[0].done)
        self.assertIsNotNone(self.store.tasks[0].completed_at)
        td.cmd_undone(self.store, 1)
        self.assertFalse(self.store.tasks[0].done)
        self.assertIsNone(self.store.tasks[0].completed_at)

    def test_rm(self):
        self.add("a")
        self.add("b")
        td.cmd_rm(self.store, 1)
        self.assertEqual([t.id for t in self.store.tasks], [2])

    def test_missing_task_raises(self):
        self.add("a")
        with self.assertRaises(KeyError):
            td.cmd_done(self.store, 99)
        with self.assertRaises(KeyError):
            td.cmd_rm(self.store, 99)

    def test_missing_store_starts_empty(self):
        self.assertEqual(self.store.tasks, [])
        self.assertEqual(self.store._next_id, 1)

    def test_corrupt_store_recovers(self):
        with open(self.store_path, "w", encoding="utf-8") as fh:
            fh.write("{ this is not json")
        store = td.Store(self.store_path).load()
        self.assertEqual(store.tasks, [])

    def test_list_filters_by_tag(self):
        self.add("one", tags=["work"])
        self.add("two", tags=["home"])
        td.cmd_done(self.store, 1)
        # after done, marker set
        self.assertTrue(self.store.tasks[0].done)


if __name__ == "__main__":
    unittest.main()
