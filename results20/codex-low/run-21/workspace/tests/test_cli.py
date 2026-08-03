import io
import unittest
from contextlib import redirect_stdout

import game_of_life.cli as cli


class CliTest(unittest.TestCase):
    def test_blinker_two_generations(self):
        buf = io.StringIO()
        with redirect_stdout(buf):
            rc = cli.main(["blinker", "-n", "2"])
        self.assertEqual(rc, 0)
        out = buf.getvalue()
        self.assertIn("gen 0", out)
        self.assertIn("gen 1", out)
        self.assertIn("OOO", out)
        self.assertIn("O", out)  # vertical phase

    def test_unknown_token_treated_as_rle(self):
        # A token that isn't a named pattern is parsed as raw RLE text.
        buf = io.StringIO()
        with redirect_stdout(buf):
            rc = cli.main(["oooo", "-n", "1"])
        self.assertEqual(rc, 0)
        self.assertIn("pop", buf.getvalue())

    def test_invalid_generation_count(self):
        buf = io.StringIO()
        with redirect_stdout(buf):
            rc = cli.main(["blinker", "-n", "0"])
        self.assertEqual(rc, 2)

    def test_raw_rle_input(self):
        buf = io.StringIO()
        with redirect_stdout(buf):
            rc = cli.main(["2o$2o!", "-n", "1"])
        self.assertEqual(rc, 0)
        self.assertIn("gen 0", buf.getvalue())


if __name__ == "__main__":
    unittest.main()
