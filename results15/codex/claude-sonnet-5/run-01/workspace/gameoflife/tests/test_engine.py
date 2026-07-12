import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from gameoflife.engine import Board
from gameoflife.patterns import PATTERNS


class BoardTests(unittest.TestCase):
    def test_empty_board_stays_empty(self):
        board = Board()
        self.assertEqual(board.step().cells, set())

    def test_block_still_life_is_stable(self):
        block = Board.from_coordinates({(0, 0), (1, 0), (0, 1), (1, 1)})
        self.assertEqual(block.step().cells, block.cells)

    def test_blinker_oscillates_with_period_two(self):
        blinker = Board.from_coordinates(PATTERNS["blinker"])
        once = blinker.step()
        twice = once.step()
        self.assertNotEqual(once.cells, blinker.cells)
        self.assertEqual(twice.cells, blinker.cells)

    def test_toad_oscillates_with_period_two(self):
        toad = Board.from_coordinates(PATTERNS["toad"])
        twice = toad.step().step()
        self.assertEqual(twice.cells, toad.cells)

    def test_lone_cell_dies(self):
        board = Board.from_coordinates({(5, 5)})
        self.assertEqual(board.step().cells, set())

    def test_overpopulated_cell_dies(self):
        board = Board.from_coordinates({(1, 1), (0, 0), (0, 1), (0, 2), (2, 1)})
        self.assertNotIn((1, 1), board.step().cells)

    def test_glider_translates_diagonally_after_four_generations(self):
        glider = Board.from_coordinates(PATTERNS["glider"])
        evolved = glider
        for _ in range(4):
            evolved = evolved.step()
        self.assertEqual(evolved.cells, glider.translated(1, 1).cells)

    def test_translated_preserves_shape(self):
        board = Board.from_coordinates({(0, 0), (1, 0)})
        shifted = board.translated(3, -2)
        self.assertEqual(shifted.cells, {(3, -2), (4, -2)})

    def test_bounding_box_of_empty_board_is_none(self):
        self.assertIsNone(Board().bounding_box())

    def test_bounding_box_covers_all_live_cells(self):
        board = Board.from_coordinates({(-1, 4), (2, -3), (0, 0)})
        self.assertEqual(board.bounding_box(), (-1, -3, 2, 4))

    def test_all_named_patterns_are_nonempty_and_evolvable(self):
        for name, coords in PATTERNS.items():
            board = Board.from_coordinates(coords)
            self.assertGreater(len(board), 0, name)
            board.step()


if __name__ == "__main__":
    unittest.main()
