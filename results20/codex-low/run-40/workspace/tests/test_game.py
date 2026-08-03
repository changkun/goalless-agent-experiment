import random
import unittest

from minesweeper.game import Board, CellState


class BoardTests(unittest.TestCase):
    def make_board(self, rows=3, cols=3, mines=1):
        return Board(rows, cols, mines, random.Random(1))

    def test_first_reveal_is_safe(self):
        board = self.make_board()
        result = board.reveal(1, 1)
        self.assertFalse(result)
        self.assertFalse(board.first_move)
        self.assertNotIn((1, 1), board.mines_positions)

    def test_mine_count_respected(self):
        board = self.make_board(4, 4, mines=5)
        board.reveal(0, 0)
        self.assertEqual(len(board.mines_positions), 5)

    def test_flag_toggle(self):
        board = self.make_board()
        board.flag(0, 0)
        self.assertEqual(board.state[0][0], CellState.FLAGGED)
        self.assertEqual(board.flagged, 1)
        board.flag(0, 0)
        self.assertEqual(board.state[0][0], CellState.HIDDEN)
        self.assertEqual(board.flagged, 0)

    def test_win_condition(self):
        board = self.make_board(2, 2, mines=1)
        board.mines_positions = {(1, 1)}
        board.counts = [[1, 1], [1, 0]]
        board.first_move = False
        self.assertFalse(board.reveal(0, 0))
        self.assertFalse(board.reveal(0, 1))
        self.assertFalse(board.reveal(1, 0))
        self.assertTrue(board.won)

    def test_out_of_bounds_flag(self):
        board = self.make_board()
        with self.assertRaises(IndexError):
            board.flag(99, 99)

    def test_negative_mines_rejected(self):
        with self.assertRaises(ValueError):
            Board(3, 3, -1)


if __name__ == "__main__":
    unittest.main()
