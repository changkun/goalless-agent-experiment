import os
import tempfile
import unittest

from streaks.cli import main


class CliTest(unittest.TestCase):
    def setUp(self):
        self.dir = tempfile.TemporaryDirectory()
        self.path = os.path.join(self.dir.name, "data.json")

    def tearDown(self):
        self.dir.cleanup()

    def test_full_flow(self):
        main(["add", "read", "--path", self.path])
        main(["check", "read", "--date", "2026-08-01", "--path", self.path])
        main(["check", "read", "--date", "2026-08-02", "--path", self.path])
        main(["check", "read", "--date", "2026-08-03", "--path", self.path])
        main(["uncheck", "read", "--date", "2026-08-02", "--path", self.path])

        with open(self.path) as fh:
            data = fh.read()
        self.assertIn("read", data)
        self.assertIn("2026-08-01", data)
        self.assertNotIn("2026-08-02", data)

    def test_remove(self):
        main(["add", "read", "--path", self.path])
        main(["check", "read", "--date", "2026-08-01", "--path", self.path])
        main(["remove", "read", "--path", self.path])
        with open(self.path) as fh:
            data = fh.read()
        self.assertNotIn("read", data)


if __name__ == "__main__":
    unittest.main()
