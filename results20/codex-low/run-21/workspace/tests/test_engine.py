import unittest

from game_of_life.engine import Board, load_pattern, parse_rle


class BoardTest(unittest.TestCase):
    def test_toggle_and_bounds(self):
        board = Board()
        board.toggle(1, -2)
        board.toggle(4, 0)
        self.assertIsNotNone(board.bounds())
        min_x, min_y, max_x, max_y = board.bounds()
        self.assertEqual((min_x, min_y, max_x, max_y), (1, -2, 4, 0))
        self.assertEqual(board.population(), 2)

    def test_empty_bounds(self):
        self.assertIsNone(Board().bounds())

    def test_block_is_still_life(self):
        board = load_pattern([(0, 0), (1, 0), (0, 1), (1, 1)])
        board.step()
        self.assertEqual(board.live, {(0, 0), (1, 0), (0, 1), (1, 1)})

    def test_blinker_oscillates(self):
        board = load_pattern([(0, 0), (1, 0), (2, 0)])
        board.step()
        self.assertEqual(board.live, {(1, -1), (1, 0), (1, 1)})
        board.step()
        self.assertEqual(board.live, {(0, 0), (1, 0), (2, 0)})

    def test_lone_cell_dies(self):
        board = load_pattern([(5, 5)])
        board.step()
        self.assertEqual(board.live, set())


class ParseRLETest(unittest.TestCase):
    def test_block(self):
        board = parse_rle("x = 2, y = 2\n2o$2o!")
        self.assertEqual(board.live, {(0, 0), (1, 0), (0, 1), (1, 1)})

    def test_glider(self):
        board = parse_rle("bo$2bo$3o!")
        expected = {(1, 0), (2, 1), (0, 2), (1, 2), (2, 2)}
        self.assertEqual(board.live, expected)


if __name__ == "__main__":
    unittest.main()
