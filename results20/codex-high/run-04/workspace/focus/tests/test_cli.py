import os
import tempfile
import unittest
from unittest import mock

import focus.cli as cli


class CliTest(unittest.TestCase):
    def setUp(self):
        self.dir = tempfile.TemporaryDirectory()
        self.env = mock.patch.dict(os.environ, {"FOCUS_DIR": self.dir.name})
        self.env.start()

    def tearDown(self):
        self.env.stop()
        self.dir.cleanup()

    def run_cli(self, *argv):
        return cli.main(list(argv))

    def test_add_list_done(self):
        self.assertEqual(self.run_cli("add", "task one", "-t", "a,b"), 0)
        self.assertEqual(self.run_cli("add", "task two"), 0)
        self.assertEqual(self.run_cli("done", "1"), 0)
        self.assertEqual(self.run_cli("list"), 0)

    def test_stats(self):
        self.run_cli("add", "first")
        self.run_cli("add", "second")
        self.assertEqual(self.run_cli("stats"), 0)

    def test_rm_and_clear(self):
        self.run_cli("add", "a")
        self.run_cli("add", "b")
        self.assertEqual(self.run_cli("rm", "1"), 0)
        self.run_cli("done", "2")
        self.assertEqual(self.run_cli("clear"), 0)

    def test_no_command_shows_help(self):
        self.assertEqual(self.run_cli(), 0)

    def test_missing_done_id(self):
        self.assertEqual(self.run_cli("done", "42"), 1)


if __name__ == "__main__":
    unittest.main()
