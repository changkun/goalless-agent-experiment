import io
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

import jsonq
from jsonq import parse_path, parse_expected, resolve, matches, PathError

SAMPLE = {
    "name": "acme",
    "users": [
        {"id": 1, "name": "alice", "role": "admin", "active": True},
        {"id": 2, "name": "bob", "role": "dev", "active": False},
        {"id": 3, "name": "carol", "role": "admin", "active": False},
    ],
}


def run_cli(args, stdin=None):
    return subprocess.run(
        [sys.executable, str(Path(__file__).parent / "jsonq.py"), *args],
        input=stdin,
        capture_output=True,
        text=True,
    )


class TestPaths(unittest.TestCase):
    def test_parse_path(self):
        self.assertEqual(parse_path("a.b[2].c"), ["a", "b", 2, "c"])
        self.assertEqual(parse_path("users[0]"), ["users", 0])

    def test_parse_path_errors(self):
        for bad in ("a[0", "a[x]"):
            with self.assertRaises(PathError):
                parse_path(bad)

    def test_resolve(self):
        self.assertEqual(resolve(SAMPLE, "users[0].name"), "alice")
        self.assertEqual(resolve(SAMPLE, "name"), "acme")
        self.assertEqual(resolve({"a": {"b": [1, 2]}}, "a.b[1]"), 2)

    def test_resolve_missing(self):
        with self.assertRaises(PathError):
            resolve(SAMPLE, "missing")

    def test_matches(self):
        self.assertTrue(matches(SAMPLE["users"][0], "role", "admin"))
        self.assertTrue(matches({"n": 1}, "n", 1))
        self.assertFalse(matches({"n": 1}, "n", 2))
        self.assertTrue(matches({"n": "1"}, "n", "1"))
        self.assertTrue(matches({"b": True}, "b", True))
        self.assertFalse(matches({"n": 1}, "missing", 1))

    def test_parse_expected(self):
        self.assertEqual(parse_expected("123"), 123)
        self.assertIs(parse_expected("true"), True)
        self.assertIsNone(parse_expected("null"))
        self.assertEqual(parse_expected("hello"), "hello")
        self.assertEqual(parse_expected("[1,2]"), [1, 2])


class TestCli(unittest.TestCase):
    def test_pretty_print_stdin(self):
        result = run_cli([], stdin='{"a":1}')
        self.assertEqual(result.returncode, 0)
        self.assertEqual(json.loads(result.stdout), {"a": 1})
        self.assertIn("  ", result.stdout)

    def test_query(self):
        result = run_cli(["-q", "users[0].name"], stdin=json.dumps(SAMPLE))
        self.assertEqual(result.returncode, 0)
        self.assertEqual(json.loads(result.stdout), "alice")

    def test_query_missing(self):
        result = run_cli(["-q", "nope"], stdin=json.dumps(SAMPLE))
        self.assertEqual(result.returncode, 2)
        self.assertIn("path not found", result.stderr)

    def test_filter_list(self):
        result = run_cli(["-f", "role=admin"], stdin=json.dumps(SAMPLE["users"]))
        self.assertEqual(result.returncode, 0)
        self.assertEqual([json.loads(line) for line in result.stdout.splitlines()],
                         [u for u in SAMPLE["users"] if u["role"] == "admin"])

    def test_filter_inspect(self):
        result = run_cli(["-f", "active=true", "-i"], stdin=json.dumps(SAMPLE["users"]))
        self.assertEqual(result.returncode, 0)
        self.assertEqual([json.loads(line) for line in result.stdout.splitlines()],
                         [u["id"] for u in SAMPLE["users"] if u["active"]])

    def test_filter_number(self):
        result = run_cli(["-f", "id=2"], stdin=json.dumps(SAMPLE["users"]))
        self.assertEqual(result.returncode, 0)
        self.assertEqual(json.loads(result.stdout), SAMPLE["users"][1])

    def test_filter_document_root(self):
        result = run_cli(["-f", "name=acme"], stdin=json.dumps(SAMPLE))
        self.assertEqual(result.returncode, 0)
        self.assertEqual(json.loads(result.stdout), SAMPLE)

    def test_file_input(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "data.json"
            path.write_text(json.dumps(SAMPLE))
            result = run_cli([str(path), "-q", "name"])
            self.assertEqual(result.returncode, 0)
            self.assertEqual(json.loads(result.stdout), "acme")

    def test_invalid_json(self):
        result = run_cli([], stdin="not json")
        self.assertEqual(result.returncode, 2)
        self.assertIn("invalid JSON", result.stderr)


if __name__ == "__main__":
    unittest.main()
