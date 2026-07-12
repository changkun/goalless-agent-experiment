import io
import tempfile
import unittest
from contextlib import redirect_stdout, redirect_stderr
from pathlib import Path

from todo.cli import main


class TestCli(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.data = Path(self.tmp.name) / "todo.json"

    def tearDown(self):
        self.tmp.cleanup()

    def _run(self, *args):
        buf = io.StringIO()
        code = main(["--data", str(self.data), *args])
        return code, buf.getvalue()

    def test_add_and_list(self):
        self.assertEqual(main(["--data", str(self.data), "add", "buy milk"]), 0)
        self.assertEqual(main(["--data", str(self.data), "add", "walk dog"]), 0)

        buf = io.StringIO()
        with redirect_stdout(buf):
            code = main(["--data", str(self.data), "list"])
        self.assertEqual(code, 0)
        output = buf.getvalue()
        self.assertIn("buy milk", output)
        self.assertIn("walk dog", output)

    def test_done_and_list_all(self):
        main(["--data", str(self.data), "add", "buy milk"])
        main(["--data", str(self.data), "done", "1"])

        buf = io.StringIO()
        with redirect_stdout(buf):
            code = main(["--data", str(self.data), "list", "--all"])
        self.assertEqual(code, 0)
        self.assertIn("[x] 1: buy milk", buf.getvalue())

    def test_remove(self):
        main(["--data", str(self.data), "add", "buy milk"])
        self.assertEqual(main(["--data", str(self.data), "remove", "1"]), 0)

        buf = io.StringIO()
        with redirect_stdout(buf):
            code = main(["--data", str(self.data), "list"])
        self.assertEqual(code, 0)
        self.assertIn("No tasks found.", buf.getvalue())

    def test_missing_done(self):
        self.assertEqual(main(["--data", str(self.data), "done", "99"]), 1)

    def test_missing_remove(self):
        self.assertEqual(main(["--data", str(self.data), "remove", "99"]), 1)


if __name__ == "__main__":
    unittest.main()
