"""Unit tests for the 2048 core logic."""

import random
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from game import Game, GameOver, Direction  # noqa: E402


class BoardTests(unittest.TestCase):
    def test_init_spawns_two_tiles(self):
        game = Game(rng=random.Random(1))
        self.assertEqual(game.moves, 0)
        self.assertEqual(game.score, 0)
        self.assertEqual(len(game.empty_cells()), 14)
        self.assertFalse(game.over)

    def test_merge_line(self):
        self.assertEqual(Game._merge_line([2, 2, 0, 0]), ([4, 0, 0, 0], 4))
        self.assertEqual(Game._merge_line([2, 2, 2, 2]), ([4, 4, 0, 0], 8))
        self.assertEqual(Game._merge_line([2, 2, 4, 4]), ([4, 8, 0, 0], 12))
        self.assertEqual(Game._merge_line([2, 4, 8, 16]), ([2, 4, 8, 16], 0))
        self.assertEqual(Game._merge_line([2, 0, 2, 0]), ([4, 0, 0, 0], 4))

    def test_slide_directions(self):
        game = Game(rng=random.Random(0))
        game.board = [[2, 2, 0, 0],
                      [0, 0, 0, 0],
                      [4, 4, 4, 4],
                      [2, 0, 2, 0]]

        moved, gained = game._slide(game.board, "left")
        self.assertTrue(moved)
        self.assertEqual(gained, 24)
        self.assertEqual(game.board, [[4, 0, 0, 0],
                                      [0, 0, 0, 0],
                                      [8, 8, 0, 0],
                                      [4, 0, 0, 0]])

    def test_no_move_returns_false(self):
        game = Game(rng=random.Random(0))
        game.board = [[2, 4, 2, 4],
                      [4, 2, 4, 2],
                      [2, 4, 2, 4],
                      [4, 2, 4, 2]]
        self.assertFalse(game.move("left"))

    def test_invalid_direction(self):
        game = Game(rng=random.Random(0))
        with self.assertRaises(ValueError):
            game._slide(game.board, "diagonal")

    def test_win_detection(self):
        game = Game(rng=random.Random(0))
        game.board[0][0] = 2048
        self.assertTrue(game._reached_win())

    def test_has_moves(self):
        game = Game(rng=random.Random(0))
        game.board = [[2, 4, 2, 4],
                      [4, 2, 4, 2],
                      [2, 4, 2, 4],
                      [4, 2, 4, 2]]
        self.assertFalse(game._has_moves())


class DirectionTests(unittest.TestCase):
    def test_resolve(self):
        self.assertEqual(Direction.resolve("w"), "up")
        self.assertEqual(Direction.resolve("A"), "left")
        self.assertEqual(Direction.resolve("up"), "up")
        self.assertEqual(Direction.resolve("right"), "right")
        self.assertIsNone(Direction.resolve("x"))
        self.assertIsNone(Direction.resolve("q"))


class SizeTests(unittest.TestCase):
    def test_custom_size(self):
        game = Game(size=3, rng=random.Random(2))
        self.assertEqual(game.size, 3)
        self.assertEqual(len(game.board), 3)

    def test_too_small(self):
        with self.assertRaises(ValueError):
            Game(size=1)


if __name__ == "__main__":
    unittest.main()
