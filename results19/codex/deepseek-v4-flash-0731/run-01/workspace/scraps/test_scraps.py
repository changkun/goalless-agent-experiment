import os
import tempfile
import unittest

from scraps import Store, add, remove, search


class ScrapsTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.path = os.path.join(self.tmp.name, "nested", "scraps.json")
        self.store = Store(self.path)

    def tearDown(self):
        self.tmp.cleanup()

    def test_add_and_load(self):
        entry = add(self.store, "hello world")
        self.assertEqual(entry["id"], 1)
        notes = self.store.load()
        self.assertEqual(len(notes), 1)
        self.assertTrue(os.path.exists(self.path))

    def test_ids_increment(self):
        add(self.store, "first")
        second = add(self.store, "second")
        self.assertEqual(second["id"], 2)

    def test_remove(self):
        add(self.store, "a")
        add(self.store, "b")
        self.assertTrue(remove(self.store, 1))
        self.assertFalse(remove(self.store, 99))
        notes = self.store.load()
        self.assertEqual([n["id"] for n in notes], [2])

    def test_search_case_insensitive(self):
        add(self.store, "Apple pie")
        add(self.store, "banana split")
        notes = self.store.load()
        self.assertEqual([n["text"] for n in search(notes, "apple")], ["Apple pie"])
        self.assertEqual(len(search(notes, "xyz")), 0)

    def test_empty_store(self):
        notes = self.store.load()
        self.assertEqual(notes, [])
        self.assertEqual(search([], "anything"), [])


if __name__ == "__main__":
    unittest.main()
