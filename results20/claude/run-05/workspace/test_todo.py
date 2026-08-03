#!/usr/bin/env python3
"""Tests for the TodoList backend (no filesystem needed)."""

import sys
import time
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import todo


class TestTodoList(unittest.TestCase):
    def setUp(self):
        self.tl = todo.TodoList()

    def test_add_and_assign_ids(self):
        a = self.tl.add("buy milk", priority="p1")
        b = self.tl.add("write report", project="work")
        self.assertEqual(a["id"], 1)
        self.assertEqual(b["id"], 2)
        self.assertEqual(a["priority"], "p1")
        self.assertIsNone(a["project"])
        self.assertEqual(b["project"], "work")

    def test_priority_defaults_and_validation(self):
        a = self.tl.add("default pri")
        self.assertEqual(a["priority"], "p3")
        b = self.tl.add("bad pri", priority="p9")
        self.assertEqual(b["priority"], "p3")

    def test_done_roundtrip_records_time(self):
        t = self.tl.add("a task")
        self.assertFalse(t["done"])
        self.assertIsNone(t["completed"])
        self.tl.set_done(t["id"], True)
        self.assertTrue(t["done"])
        self.assertIsNotNone(t["completed"])
        self.tl.set_done(t["id"], False)
        self.assertFalse(t["done"])
        self.assertIsNone(t["completed"])

    def test_visible_filters_and_sort(self):
        p3 = self.tl.add("low", priority="p3")
        p1 = self.tl.add("high", priority="p1")
        w = self.tl.add("work thing", project="work")
        self.tl.set_done(p3["id"], True)

        # open tasks only, sorted by priority ascending (p1 first)
        vis = self.tl.visible()
        self.assertEqual([t["id"] for t in vis], [p1["id"], w["id"]])

        # include done
        vis_all = self.tl.visible(include_done=True)
        self.assertEqual(len(vis_all), 3)

        # project filter
        vis_w = self.tl.visible(project="work")
        self.assertEqual([t["id"] for t in vis_w], [w["id"]])

    def test_find_and_remove(self):
        t = self.tl.add("temp")
        self.assertIsNotNone(self.tl.find(t["id"]))
        removed = self.tl.remove(t["id"])
        self.assertEqual(removed["text"], "temp")
        self.assertIsNone(self.tl.find(t["id"]))
        self.assertIsNone(self.tl.remove(9999))

    def test_load_resumes_id_counter(self):
        self.tl.add("one")
        self.tl.add("two")
        # simulate round-trip through JSON (as TodoList.load() does)
        data = {"tasks": self.tl.tasks}
        tl2 = todo.TodoList(json_copy(data["tasks"]))
        nxt = tl2.add("three")
        self.assertEqual(nxt["id"], 3)


def json_copy(tasks):
    import copy
    return copy.deepcopy(tasks)


if __name__ == "__main__":
    unittest.main()
