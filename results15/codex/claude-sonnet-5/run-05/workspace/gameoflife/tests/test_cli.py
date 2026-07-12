import io
import unittest
from contextlib import redirect_stdout

from gameoflife.cli import run


class CliTests(unittest.TestCase):
    def test_run_completes_without_error(self):
        buffer = io.StringIO()
        with redirect_stdout(buffer):
            exit_code = run(
                ["--pattern", "blinker", "--generations", "3", "--interval", "0", "--no-clear"]
            )
        output = buffer.getvalue()
        self.assertEqual(exit_code, 0)
        self.assertIn("Generation 0", output)
        self.assertIn("Generation 3", output)


if __name__ == "__main__":
    unittest.main()
