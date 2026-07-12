import unittest

from gol.board import Board
from gol.patterns import PATTERNS


class PatternTests(unittest.TestCase):
    def test_all_patterns_parse_to_nonempty_boards(self):
        for name, pattern in PATTERNS.items():
            board = Board.from_pattern(pattern)
            self.assertGreater(len(board), 0, f"pattern {name!r} produced an empty board")

    def test_glider_pattern_has_five_live_cells(self):
        board = Board.from_pattern(PATTERNS["glider"])
        self.assertEqual(len(board), 5)


if __name__ == "__main__":
    unittest.main()
