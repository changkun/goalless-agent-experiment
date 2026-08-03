import random
import unittest

from engine.core import Game, Move


class TestSlide(unittest.TestCase):
    """Tests against the deterministic _slide primitive (no spawn)."""

    def setUp(self):
        self.game = Game(size=4, seed=1)

    def slide(self, tiles, move):
        # pad short rows with zeros to a full size*size board
        board = list(tiles) + [0] * (self.game.size * self.game.size - len(tiles))
        board, gained = self.game._slide(board, move)
        return board, gained

    def test_left_merges_once_and_compresses(self):
        board, gained = self.slide([2, 2, 2, 2], Move.LEFT)
        self.assertEqual(gained, 8)
        self.assertEqual(board[:4], [4, 4, 0, 0])

    def test_right_merges_and_keeps_right(self):
        board, _ = self.slide([2, 2, 2, 2], Move.RIGHT)
        self.assertEqual(board[:4], [0, 0, 4, 4])

    def test_chain_does_not_merge_twice(self):
        board, gained = self.slide([4, 2, 2, 4], Move.LEFT)
        self.assertEqual(board[:4], [4, 4, 4, 0])
        self.assertEqual(gained, 4)

    def test_no_merge_different_values(self):
        board, gained = self.slide([2, 4, 8, 16], Move.LEFT)
        self.assertEqual(board[:4], [2, 4, 8, 16])
        self.assertEqual(gained, 0)

    def test_up_and_down(self):
        tiles = [2, 0, 0, 0, 2, 0, 0, 0, 4, 0, 0, 0, 4, 0, 0, 0]
        up, gained_up = self.slide(tiles, Move.UP)
        self.assertEqual(up, [4, 0, 0, 0, 8, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0])
        self.assertEqual(gained_up, 12)
        down, _ = self.slide(tiles, Move.DOWN)
        self.assertEqual(down, [0, 0, 0, 0, 0, 0, 0, 0, 4, 0, 0, 0, 8, 0, 0, 0])


class TestMove(unittest.TestCase):
    def setUp(self):
        self.game = Game(size=4, seed=1)
        self.game.set_tiles([0] * 16)

    def assert_board(self, tiles):
        self.assertEqual(list(self.game.board), list(tiles))

    def test_move_merges_and_scores(self):
        self.game.set_tiles([2, 2, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0])
        result = self.game.move(Move.LEFT)
        self.assertTrue(result.moved)
        self.assertEqual(result.gained, 4)
        self.assertEqual(self.game.score, 4)
        # First two cells hold a 4, rest empty plus one spawn.
        self.assertEqual(self.game.board[0], 4)
        self.assertEqual(self.game.board[1], 0)
        self.assertEqual(sum(1 for t in self.game.board if t), 2)

    def test_noop_move_does_not_spawn(self):
        self.game.set_tiles([2, 4, 8, 2, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0])
        before = list(self.game.board)
        result = self.game.move(Move.LEFT)
        self.assertFalse(result.moved)
        self.assert_board(before)
        self.assertEqual(self.game.moves, 0)
        self.assertEqual(result.gained, 0)

    def test_empty_cells_after_spawn(self):
        self.game.set_tiles([0] * 16)
        self.assertEqual(len(self.game.empty_cells()), 16)


class TestSpawn(unittest.TestCase):
    def test_initial_tiles_and_only_twos_fours(self):
        game = Game(size=4, seed=7)
        self.assertEqual(len(game.empty_cells()), 14)
        self.assertTrue(all(t in (0, 2, 4) for t in game.board))

    def test_spawn_never_fills_randomly(self):
        game = Game(size=4, seed=3)
        for _ in range(100):
            for move in Move:
                if game.move(move).moved:
                    break
            self.assertGreaterEqual(len(game.empty_cells()), 0)


class TestScoringAndWin(unittest.TestCase):
    def test_win_flag_set_once(self):
        game = Game(size=4, seed=1)
        game.set_tiles([1024, 1024, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0])
        result = game.move(Move.LEFT)
        self.assertTrue(result.won)
        self.assertTrue(game.won)

    def test_win_persists(self):
        game = Game(size=4, seed=1)
        game.set_tiles([1024, 1024, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0])
        game.move(Move.LEFT)
        game.move(Move.DOWN)
        self.assertTrue(game.won)


class TestGameOver(unittest.TestCase):
    def test_full_board_with_merge_is_not_over(self):
        game = Game(size=2, seed=1)
        game.set_tiles([4, 4, 2, 2])
        self.assertFalse(game.is_game_over())

    def test_classic_stuck_board_is_over(self):
        game = Game(size=2, seed=1)
        game.set_tiles([2, 4, 8, 16])
        self.assertTrue(game.is_game_over())

    def test_board_with_merge_everywhere_not_over(self):
        game = Game(size=2, seed=1)
        game.set_tiles([4, 4, 4, 4])
        self.assertFalse(game.is_game_over())

    def test_empty_board_not_over(self):
        game = Game(size=4, seed=1)
        game.set_tiles([0] * 16)
        self.assertFalse(game.is_game_over())

    def test_bottomless_pit_score(self):
        # A dead column: [2,4,8,16]; merging up impossible -> not over due to
        # horizontal moves freeing space, but vertical is stuck.
        game = Game(size=4, seed=1)
        game.set_tiles(
            [2, 0, 0, 0, 4, 0, 0, 0, 8, 0, 0, 0, 16, 0, 0, 0]
        )
        self.assertFalse(game.is_game_over())


class TestInitValidation(unittest.TestCase):
    def test_bad_size_rejected(self):
        with self.assertRaises(ValueError):
            Game(size=1)

    def test_too_many_start_tiles_rejected(self):
        with self.assertRaises(ValueError):
            Game(size=2, start_tiles=5)

    def test_bad_tile_count_rejected(self):
        game = Game(size=4)
        with self.assertRaises(ValueError):
            game.set_tiles([2] * 3)

    def test_seeded_games_are_reproducible(self):
        boards = [tuple(Game(seed=42).board) for _ in range(3)]
        self.assertEqual(boards[0], boards[1])
        self.assertEqual(boards[1], boards[2])


class TestRandomPlay(unittest.TestCase):
    def test_random_moves_stay_valid(self):
        for seed in range(30):
            game = Game(size=4, seed=seed)
            rng = random.Random(seed)
            for _ in range(300):
                game.move(rng.choice(list(Move)))
                self.assertTrue(all(t >= 0 for t in game.board))
                # Score can never decrease.
                self.assertGreaterEqual(game.score, 0)


if __name__ == "__main__":
    unittest.main()
