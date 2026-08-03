import unittest

from game2048.logic import (
    DOWN,
    LEFT,
    RIGHT,
    UP,
    add_random_tile,
    blank_board,
    can_move,
    has_won,
    move,
)


class SlideRowTest(unittest.TestCase):
    def test_merge_equals_and_compact(self):
        from game2048.logic import _slide_row

        board = [[2, 2, 0, 2], [0, 0, 0, 0], [0, 0, 0, 0], [0, 0, 0, 0]]
        moved, score, changed = move(board, LEFT)
        self.assertEqual(moved, [[4, 2, 0, 0], [0, 0, 0, 0], [0, 0, 0, 0], [0, 0, 0, 0]])
        self.assertEqual(score, 4)
        self.assertTrue(changed)


class MoveTest(unittest.TestCase):
    def test_left(self):
        board = [[2, 2, 0, 4], [0, 0, 0, 0], [0, 0, 0, 0], [0, 0, 0, 0]]
        moved, score, changed = move(board, LEFT)
        self.assertEqual(moved[0], [4, 4, 0, 0])
        self.assertEqual(score, 4)
        self.assertTrue(changed)

    def test_right(self):
        board = [[2, 2, 2, 2], [0, 0, 0, 0], [0, 0, 0, 0], [0, 0, 0, 0]]
        moved, score, changed = move(board, RIGHT)
        self.assertEqual(moved[0], [0, 0, 4, 4])
        self.assertEqual(score, 8)

    def test_up(self):
        board = [[2, 0, 0, 0], [2, 0, 0, 0], [0, 0, 0, 0], [0, 0, 0, 0]]
        moved, score, _ = move(board, UP)
        self.assertEqual([row[0] for row in moved], [4, 0, 0, 0])
        self.assertEqual(score, 4)

    def test_down(self):
        board = [[2, 0, 0, 0], [2, 0, 0, 0], [0, 0, 0, 0], [0, 0, 0, 0]]
        moved, score, _ = move(board, DOWN)
        self.assertEqual([row[0] for row in moved], [0, 0, 0, 4])
        self.assertEqual(score, 4)

    def test_no_change(self):
        board = [[2, 4, 8, 16], [0, 0, 0, 0], [0, 0, 0, 0], [0, 0, 0, 0]]
        _, score, changed = move(board, LEFT)
        self.assertEqual(score, 0)
        self.assertFalse(changed)

    def test_mutates_in_place(self):
        board = [[2, 2, 0, 0], [0, 0, 0, 0], [0, 0, 0, 0], [0, 0, 0, 0]]
        returned, _, _ = move(board, LEFT)
        self.assertIs(returned, board)
        self.assertEqual(board[0][0], 4)


class RandomTileTest(unittest.TestCase):
    class _FakeRng:
        """Returns a fixed cell index then a fixed spawn digit."""

        def __init__(self, cell_index, spawn_digit):
            self.cell_index = cell_index
            self.spawn_digit = spawn_digit
            self.calls = 0

        def __call__(self, a, b):
            self.calls += 1
            return self.cell_index if self.calls == 1 else self.spawn_digit

    def test_places_tile(self):
        board = blank_board()
        rng = self._FakeRng(0, 9)  # digit 9 -> spawn a 4
        add_random_tile(board, rng)
        self.assertEqual(board[0][0], 4)


class EndConditionsTest(unittest.TestCase):
    def test_has_won(self):
        board = blank_board()
        board[0][0] = 2048
        self.assertTrue(has_won(board))

    def test_can_move_with_empty(self):
        self.assertTrue(can_move(blank_board()))

    def test_can_move_no_moves(self):
        board = [[2, 4, 8, 16], [16, 8, 4, 2], [2, 4, 8, 16], [16, 8, 4, 2]]
        self.assertFalse(can_move(board))

    def test_can_move_with_adjacent_equal(self):
        board = [[2, 2, 8, 16], [16, 8, 4, 2], [2, 4, 8, 16], [16, 8, 4, 2]]
        self.assertTrue(can_move(board))


if __name__ == "__main__":
    unittest.main()
