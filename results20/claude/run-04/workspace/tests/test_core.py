"""Tests for memo's core.py (no CLI, no disk-by-default)."""

import json
import os
import tempfile
import unittest

from memo import MemoStore
from memo.core import MemoError, parse_tags, _next_id


def _ids(memos):
    return [m.id for m in memos]


class ParseTagsTest(unittest.TestCase):
    def test_extracts_lowercased_unique_tags(self):
        self.assertEqual(parse_tags("Hi #Work and #work and #Today!"), ["work", "today"])

    def test_ignores_hash_not_preceding_word(self):
        self.assertEqual(parse_tags("no tag here"), [])
        self.assertEqual(parse_tags("a #1b"), ["1b"])  # digit-leading ok
        self.assertEqual(parse_tags("hash not followed by a word: a # b"), [])

    def test_supports_hierarchy_separators(self):
        self.assertEqual(parse_tags("#work/deep and #a.b #c_d"), ["work/deep", "a.b", "c_d"])


class StoreTest(unittest.TestCase):
    def setUp(self):
        self.dir = tempfile.mkdtemp()
        self.path = os.path.join(self.dir, "memo.json")
        self.store = MemoStore(self.path)

    def tearDown(self):
        if os.path.exists(self.dir):
            for f in os.listdir(self.dir):
                os.unlink(os.path.join(self.dir, f))
            os.rmdir(self.dir)

    def test_add_and_roundtrip(self):
        m = self.store.add("Buy oat milk #errands #today")
        self.assertEqual(m.tags, ["errands", "today"])
        again = MemoStore(self.path)
        rows = again.all()
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0].text, "Buy oat milk #errands #today")

    def test_rejects_empty(self):
        with self.assertRaises(MemoError):
            self.store.add("   ")

    def test_creates_file_lazily(self):
        self.assertFalse(os.path.exists(self.path))
        self.store.add("hello #a")
        self.assertTrue(os.path.exists(self.path))

    def test_search_and_prefix(self):
        self.store.add("deep work #work/deep")
        self.store.add("standup #work/meetings")
        self.store.add("gym #health")
        self.assertEqual(len(self.store.search(["work"])), 0)          # no literal #work
        self.assertEqual(len(self.store.search(["work"], prefix=True)), 2)
        self.assertEqual(len(self.store.search(["health"])), 1)

    def test_all_tags_required_and_ordering(self):
        self.store.add("a #x #y", ts=1.0)
        self.store.add("b #x", ts=2.0)
        self.store.add("c #y", ts=3.0)
        self.assertEqual(_ids(self.store.search(["x", "y"])), [self.store.all()[0].id])
        # newest first across the whole store
        self.assertEqual(_ids(self.store.search()), [self.store.all()[2].id, self.store.all()[1].id, self.store.all()[0].id])

    def test_delete(self):
        m = self.store.add("temp #t")
        self.assertTrue(self.store.delete(m.id))
        self.assertFalse(self.store.delete(m.id))
        self.assertEqual(self.store.all(), [])

    def test_tags_frequency_ordering(self):
        self.store.add("one #a #b")
        self.store.add("two #b #b #c")
        self.assertEqual(self.store.tags()[0], "b")

    def test_corrupt_file_raises(self):
        with open(self.path, "w") as fh:
            fh.write("{not json")
        with self.assertRaises(MemoError):
            self.store.all()

    def test_ids_unique(self):
        self.assertNotEqual(_next_id(), _next_id())

    def test_import(self):
        n = self.store.import_text(["first line", "", "  ", "second line"])
        self.assertEqual(n, 2)
        self.assertEqual(len(self.store.all()), 2)


class AtomicityTest(unittest.TestCase):
    def test_save_leaves_valid_json_on_success(self):
        with tempfile.TemporaryDirectory() as d:
            p = os.path.join(d, "m.json")
            s = MemoStore(p)
            s.add("hello #x")
            s.add("world #y")
            with open(p) as fh:
                data = json.load(fh)
            self.assertEqual(len(data), 2)
            self.assertEqual(data[0]["tags"], ["x"])  # newest appended last


if __name__ == "__main__":
    unittest.main()
