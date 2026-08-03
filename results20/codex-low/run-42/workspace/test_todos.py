import json
import tempfile
import unittest
from pathlib import Path

import todos


def make_file(todos_list):
    d = tempfile.mkdtemp()
    path = Path(d) / "todos.json"
    path.write_text(json.dumps(todos_list), encoding="utf-8")
    return path


def run(argv, path):
    old = todos.os.environ.get(todos.STORAGE_ENV)
    todos.os.environ[todos.STORAGE_ENV] = str(path)
    try:
        return todos.main(argv)
    finally:
        if old is None:
            todos.os.environ.pop(todos.STORAGE_ENV, None)
        else:
            todos.os.environ[todos.STORAGE_ENV] = old


class TodoTests(unittest.TestCase):
    def test_add_and_list(self):
        path = make_file([])
        self.assertEqual(run(["add", "hello"], path), 0)
        data = json.loads(path.read_text(encoding="utf-8"))
        self.assertEqual(data, [{"text": "hello", "priority": "medium",
                                 "created": todos.date.today().isoformat(),
                                 "completed": False}])

    def test_done_updates_completion(self):
        path = make_file([{"text": "a", "priority": "medium", "completed": False}])
        self.assertEqual(run(["done", "1"], path), 0)
        data = json.loads(path.read_text(encoding="utf-8"))
        self.assertTrue(data[0]["completed"])

    def test_done_with_bad_id_fails(self):
        path = make_file([{"text": "a", "priority": "medium", "completed": False}])
        self.assertEqual(run(["done", "99"], path), 1)

    def test_clear(self):
        path = make_file([{"text": "a", "priority": "high", "completed": False}])
        self.assertEqual(run(["clear"], path), 0)
        self.assertEqual(json.loads(path.read_text(encoding="utf-8")), [])

    def test_load_creates_empty_list_for_missing_file(self):
        d = tempfile.mkdtemp()
        self.assertEqual(todos.load(Path(d) / "nope.json"), [])


if __name__ == "__main__":
    unittest.main()
