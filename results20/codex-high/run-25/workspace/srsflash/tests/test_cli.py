import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from srsflash.cli import main  # noqa: E402


class CliTests(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.TemporaryDirectory()
        self.deck = os.path.join(self.tmpdir.name, "deck.json")

    def tearDown(self):
        self.tmpdir.cleanup()

    def test_add(self):
        self.assertEqual(main(["--deck", self.deck, "add", "Q", "A"]), 0)
        self.assertTrue(os.path.exists(self.deck))

    def test_remove_invalid_index(self):
        self.assertEqual(main(["--deck", self.deck, "remove", "5"]), 1)


if __name__ == "__main__":
    unittest.main()
