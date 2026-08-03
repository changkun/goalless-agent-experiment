import random
import unittest

from game2048.core import Game, SIZE


def board(g):
    return g.board


def set_board(g, rows):
    g.board = [list(row) for row in rows]


class TestMoves(unittest.TestCase):
    def test_slide_and_merge_left(self):
        g = Game(rng=random.Random(0))
        set_board(g, [[2, 2, 2, 2], [0, 0, 0, 0], [0, 0, 0, 0], [0, 0, 0, 0]])
        g.move("left")
        self.assertEqual(board(g)[0], [4, 4, 0, 0])

    def test_merge_once(self):
        g = Game(rng=random.Random(0))
        set_board(g, [[2, 2, 2, 0], [0, 0, 0, 0], [0, 0, 0, 0], [0, 0, 0, 0]])
        g.move("left")
        self.assertEqual(board(g)[0], [4, 2, 0, 0])

    def test_right(self):
        g = Game(rng=random.Random(0))
        set_board(g, [[2, 2, 2, 2], [0, 0, 0, 0], [0, 0, 0, 0], [0, 0, 0, 0]])
        g.move("right")
        self.assertEqual(board(g)[0], [0, 0, 4, 4])

    def test_up(self):
        g = Game(rng=random.Random(0))
        set_board(g, [[2, 0, 0, 0], [2, 0, 0, 0], [0, 0, 0, 0], [0, 0, 0, 0]])
        g.move("up")
        self.assertEqual(board(g)[0], [4, 0, 0, 0])

    def test_down(self):
        g = Game(rng=random.Random(0))
        set_board(g, [[0, 0, 0, 4], [0, 0, 0, 4], [0, 0, 0, 0], [0, 0, 0, 0]])
        g.move("down")
        self.assertEqual(board(g)[3], [0, 0, 0, 8])

    def test_score(self):
        g = Game(rng=random.Random(0))
        set_board(g, [[2, 2, 0, 0], [0, 0, 0, 0], [0, 0, 0, 0], [0, 0, 0, 0]])
        g.move("left")
        self.assertEqual(g.score, 4)

    def test_no_change_returns_false(self):
        g = Game(rng=random.Random(0))
        set_board(g, [[2, 4, 8, 16] for _ in range(SIZE)])
        before = board(g)
        self.assertFalse(g.move("left"))
        self.assertEqual(board(g), before)

    def test_invalid_direction(self):
        g = Game(rng=random.Random(0))
        with self.assertRaises(ValueError):
            g.move("diagonal")


class TestLifecycle(unittest.TestCase):
    def test_spawns_two_tiles(self):
        g = Game(rng=random.Random(1))
        self.assertEqual(len(g._empty_cells()), SIZE * SIZE - 2)

    def test_game_over(self):
        g = Game(rng=random.Random(0))
        set_board(g, [
            [2, 4, 2, 4],
            [4, 2, 4, 2],
            [2, 4, 2, 4],
            [4, 2, 4, 2],
        ])
        self.assertTrue(g.is_game_over())
        self.assertFalse(g.can_move())

    def test_has_won(self):
        g = Game(rng=random.Random(0))
        set_board(g, [[2048, 0, 0, 0], [0, 0, 0, 0], [0, 0, 0, 0], [0, 0, 0, 0]])
        self.assertTrue(g.has_won())
        self.assertFalse(g.has_won(target=4096))


if __name__ == "__main__":
    unittest.main()
