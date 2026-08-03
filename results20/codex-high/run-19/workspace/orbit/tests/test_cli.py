import io
import unittest
from contextlib import redirect_stderr, redirect_stdout

from orbit.cli import main


class CliTests(unittest.TestCase):
    def test_show_one_planet(self) -> None:
        out = io.StringIO()
        with redirect_stdout(out):
            code = main(["mars"])
        self.assertEqual(code, 0)
        self.assertIn("Mars", out.getvalue())

    def test_show_all_by_default(self) -> None:
        out = io.StringIO()
        with redirect_stdout(out):
            code = main([])
        self.assertEqual(code, 0)
        self.assertEqual(out.getvalue().count("Did you know?"), 8)

    def test_unknown_planet_returns_error_without_output(self) -> None:
        out, err = io.StringIO(), io.StringIO()
        with redirect_stdout(out):
            with redirect_stderr(err):
                code = main(["pluto"])
        self.assertEqual(code, 1)
        self.assertEqual(out.getvalue(), "")
        self.assertIn("Unknown planet", err.getvalue())

    def test_partial_unknown_still_works(self) -> None:
        out, err = io.StringIO(), io.StringIO()
        with redirect_stdout(out):
            with redirect_stderr(err):
                code = main(["mars", "pluto"])
        self.assertEqual(code, 0)
        self.assertIn("Mars", out.getvalue())
        self.assertIn("Unknown planet", err.getvalue())


if __name__ == "__main__":
    unittest.main()
