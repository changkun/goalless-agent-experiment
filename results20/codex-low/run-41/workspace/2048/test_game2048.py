import unittest

from game2048 import Game


def full_grid(rows):
    """Build a 4x4 grid from the top rows, zero-filling the rest."""
    g = Game(seed=1)
    g.grid = [r + [0] * (4 - len(r)) for r in rows]
    g.grid += [[0] * 4 for _ in range(4 - len(g.grid))]
    return g


class SlideTests(unittest.TestCase):
    def test_compress_left(self):
        g = Game(seed=1)
        g.grid = [[2, 0, 2, 4], [0, 0, 0, 0], [0, 0, 0, 0], [0, 0, 0, 0]]
        g.move("left")
        # [4,4,0,0] plus a random spawned tile somewhere in the 2 zero cells
        self.assertEqual(g.grid[0][:2], [4, 4])
        self.assertEqual(g.grid[0][2:], [0, 0])

    def test_merge_chain_only_used_once(self):
        merged, gained = Game._slide_row([2, 2, 2, 2])
        self.assertEqual(merged, [4, 4, 0, 0])
        self.assertEqual(gained, 8)

    def test_merge_priority_left(self):
        merged, _ = Game._slide_row([4, 4, 8, 0])
        self.assertEqual(merged, [8, 8, 0, 0])

    def test_move_right(self):
        g = Game(seed=1)
        g.grid = [[2, 0, 2, 4], [0, 0, 0, 0], [0, 0, 0, 0], [0, 0, 0, 0]]
        g.move("right")
        self.assertEqual(g.grid[0][:2], [0, 0])
        self.assertEqual(g.grid[0][2], 4)

    def test_move_up(self):
        g = Game(seed=1)
        g.grid = [[2, 0, 0, 0], [2, 0, 0, 0], [0, 0, 0, 0], [0, 0, 0, 0]]
        g.move("up")
        self.assertEqual(g.grid[0][0], 4)  # merged 2+2=4

    def test_move_down(self):
        g = Game(seed=1)
        g.grid = [[2, 0, 0, 0], [2, 0, 0, 0], [0, 0, 0, 0], [0, 0, 0, 0]]
        g.move("down")
        self.assertEqual(g.grid[3][0], 4)  # merged 2+2=4 at bottom

    def test_still_move_returns_false_no_spawn(self):
        g = Game(seed=1)
        g.grid = [[2, 0, 0, 0], [2, 0, 0, 0], [0, 0, 0, 0], [0, 0, 0, 0]]
        g.move("left")  # merges top row 2+2=4
        before = [r[:] for r in g.grid]
        changed = g.move("left")  # no movement on second call
        self.assertFalse(changed)
        self.assertEqual(g.grid, before)  # no new tile spawned


class GameLogicTests(unittest.TestCase):
    def test_new_game_has_two_tiles(self):
        g = Game(seed=5)
        self.assertEqual(sum(1 for r in g.grid for v in r if v), 2)
        self.assertEqual(g.score, 0)

    def test_merge_scores(self):
        g = Game(seed=1)
        g.grid = [[2, 0, 2, 4], [0, 0, 0, 0], [0, 0, 0, 0], [0, 0, 0, 0]]
        g.move("left")  # 2+2 = 4 points
        self.assertEqual(g.score, 4)

    def test_no_moves_means_game_over(self):
        # Checkerboard: no equal neighbors and no zeros -> no moves.
        g = Game(seed=1)
        g.grid = [
            [2, 4, 2, 4],
            [4, 2, 4, 2],
            [2, 4, 2, 4],
            [4, 2, 4, 2],
        ]
        self.assertFalse(g._moves_available())

    def test_goal_won(self):
        g = Game(seed=1, goal=8)
        g.grid = [[4, 4, 0, 0], [0, 0, 0, 0], [0, 0, 0, 0], [0, 0, 0, 0]]
        g.move("left")  # 4+4=8 reaches goal
        self.assertTrue(g.won)


if __name__ == "__main__":
    unittest.main()
