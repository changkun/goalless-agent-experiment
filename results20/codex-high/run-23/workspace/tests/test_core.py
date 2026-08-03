import unittest

from game2048 import Board, Direction


def make_board(grid, rng=None):
    b = Board(size=len(grid), rng=rng)
    b.grid = [row[:] for row in grid]
    b.score = 0
    return b


class TestCompress(unittest.TestCase):
    def test_merge_left(self):
        b = make_board([[2, 2, 0, 0], [0, 0, 0, 0], [0, 0, 0, 0], [0, 0, 0, 0]])
        res = b.move(Direction.LEFT)
        self.assertTrue(res.moved)
        self.assertEqual(b.grid[0], [4, 0, 0, 0])
        self.assertEqual(res.score_gained, 4)

    def test_double_merge(self):
        b = make_board([[2, 2, 2, 2], [0, 0, 0, 0], [0, 0, 0, 0], [0, 0, 0, 0]])
        b.move(Direction.LEFT)
        self.assertEqual(b.grid[0], [4, 4, 0, 0])

    def test_move_right(self):
        b = make_board([[2, 2, 0, 0], [0, 0, 0, 0], [0, 0, 0, 0], [0, 0, 0, 0]])
        b.move(Direction.RIGHT)
        self.assertEqual(b.grid[0], [0, 0, 0, 4])

    def test_move_up(self):
        b = make_board([[2, 0, 0, 0], [2, 0, 0, 0], [0, 0, 0, 0], [0, 0, 0, 0]])
        b.move(Direction.UP)
        self.assertEqual([b.grid[r][0] for r in range(4)], [4, 0, 0, 0])

    def test_no_move(self):
        b = make_board([[2, 4, 2, 4], [4, 2, 4, 2], [2, 4, 2, 4], [4, 2, 4, 2]])
        res = b.move(Direction.LEFT)
        self.assertFalse(res.moved)
        self.assertFalse(res.spawned)

    def test_blocked_merge_order(self):
        # 4,2,2 moving left should merge the 2s, not the leading 4.
        b = make_board([[4, 2, 2, 0], [0, 0, 0, 0], [0, 0, 0, 0], [0, 0, 0, 0]])
        b.move(Direction.LEFT)
        self.assertEqual(b.grid[0], [4, 4, 0, 0])


class TestSpawn(unittest.TestCase):
    def test_spawn_values(self):
        import random

        b = Board(size=4, rng=random.Random(1))
        values = [v for row in b.grid for v in row if v]
        self.assertTrue(all(v in (2, 4) for v in values))
        self.assertEqual(len(values), 2)

    def test_spawn_fills_only_empty(self):
        b = make_board([[2, 2, 2, 2], [2, 2, 2, 2], [2, 2, 2, 2], [2, 2, 2, 0]])
        before = [v for row in b.grid for v in row].count(0)
        b.spawn_tile()
        after = [v for row in b.grid for v in row].count(0)
        self.assertEqual(after, before - 1)


class TestGameOver(unittest.TestCase):
    def test_full_no_moves(self):
        b = make_board([[2, 4, 2, 4], [4, 2, 4, 2], [2, 4, 2, 4], [4, 2, 4, 2]])
        self.assertFalse(b.can_move())

    def test_full_but_mergable(self):
        b = make_board([[2, 2, 4, 8], [16, 32, 64, 128], [256, 512, 1024, 2048], [4, 8, 16, 32]])
        self.assertTrue(b.can_move())


class TestWin(unittest.TestCase):
    def test_is_won(self):
        b = make_board([[2048, 0, 0, 0], [0, 0, 0, 0], [0, 0, 0, 0], [0, 0, 0, 0]])
        self.assertTrue(b.is_won())
        self.assertEqual(b.max_tile(), 2048)


if __name__ == "__main__":
    unittest.main()
