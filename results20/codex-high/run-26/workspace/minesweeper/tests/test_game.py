import random
import unittest

from minesweeper.game import Board, GameOver, GameWon


class BoardTest(unittest.TestCase):
    def test_dimensions_validation(self):
        with self.assertRaises(ValueError):
            Board(0, 9, 1)
        with self.assertRaises(ValueError):
            Board(9, 9, 100)

    def test_mine_count(self):
        board = Board(4, 4, 3, random.Random(0))
        total = sum(1 for row in board.cells for cell in row if cell.mine)
        self.assertEqual(total, 3)

    def test_reveal_empty_floods(self):
        board = Board(1, 1, 0, random.Random(0))
        with self.assertRaises(GameWon):
            board.reveal(0, 0)

    def test_out_of_bounds(self):
        board = Board(3, 3, 1, random.Random(0))
        with self.assertRaises(IndexError):
            board.reveal(9, 9)

    def test_flag_blocks_reveal(self):
        board = Board(2, 2, 0, random.Random(0))
        board.toggle_flag(0, 0)
        self.assertTrue(board.cells[0][0].flagged)
        board.reveal(0, 0)
        self.assertFalse(board.cells[0][0].revealed)

    def test_hitting_mine_raises(self):
        board = Board(2, 2, 1, random.Random(1))
        mine_cell = None
        for r in range(2):
            for c in range(2):
                if board.cells[r][c].mine:
                    mine_cell = (r, c)
        with self.assertRaises(GameOver):
            board.reveal(*mine_cell)

    def test_reveal_all_safe_raises_won(self):
        board = Board(2, 2, 1, random.Random(0))
        safe = [(r, c) for r in range(2) for c in range(2)
                if not board.cells[r][c].mine]
        raised = False
        try:
            for r, c in safe:
                board.reveal(r, c)
        except GameWon:
            raised = True
        self.assertTrue(raised)


if __name__ == "__main__":
    unittest.main()
