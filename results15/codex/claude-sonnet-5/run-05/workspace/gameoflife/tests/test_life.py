import unittest

from gameoflife.life import Board
from gameoflife.patterns import BLINKER, GLIDER, TOAD


class BoardTests(unittest.TestCase):
    def test_from_pattern_parses_live_cells(self):
        board = Board.from_pattern(["#.", ".#"])
        self.assertEqual(board.live_cells, {(0, 0), (1, 1)})

    def test_blinker_oscillates_with_period_two(self):
        board = Board.from_pattern(BLINKER)
        step1 = board.step()
        step2 = step1.step()
        self.assertEqual(step2.live_cells, board.live_cells)
        self.assertNotEqual(step1.live_cells, board.live_cells)

    def test_toad_oscillates_with_period_two(self):
        board = Board.from_pattern(TOAD)
        step1 = board.step()
        step2 = step1.step()
        self.assertEqual(step2.live_cells, board.live_cells)

    def test_glider_translates_after_four_steps(self):
        board = Board.from_pattern(GLIDER)
        result = board
        for _ in range(4):
            result = result.step()

        shifted = {(r + 1, c + 1) for r, c in board.live_cells}
        self.assertEqual(result.live_cells, shifted)

    def test_lonely_cell_dies(self):
        board = Board(live_cells={(5, 5)})
        self.assertEqual(board.step().live_cells, set())

    def test_empty_board_stays_empty(self):
        board = Board()
        self.assertEqual(board.step().live_cells, set())

    def test_still_life_block_is_stable(self):
        block = {(0, 0), (0, 1), (1, 0), (1, 1)}
        board = Board(live_cells=block)
        self.assertEqual(board.step().live_cells, block)

    def test_generation_counter_increments(self):
        board = Board.from_pattern(BLINKER)
        self.assertEqual(board.generation, 0)
        self.assertEqual(board.step().generation, 1)

    def test_render_produces_expected_grid(self):
        board = Board.from_pattern(["#."])
        self.assertEqual(board.render(), "#")

    def test_bounding_box_raises_on_empty_board(self):
        board = Board()
        with self.assertRaises(ValueError):
            board.bounding_box()


if __name__ == "__main__":
    unittest.main()
