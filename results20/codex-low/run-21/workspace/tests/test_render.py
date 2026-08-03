import unittest

from game_of_life.engine import load_pattern
from game_of_life.render import render, render_at


class RenderTest(unittest.TestCase):
    def test_render_block(self):
        board = load_pattern([(0, 0), (1, 0), (0, 1), (1, 1)])
        self.assertEqual(render(board), "OO\nOO")

    def test_render_empty(self):
        self.assertEqual(render(load_pattern([])), "")

    def test_render_custom_chars(self):
        board = load_pattern([(0, 0)])
        self.assertEqual(render(board, alive="#", dead="_"), "#")

    def test_render_at_window(self):
        board = load_pattern([(0, 0)])
        out = render_at(board, size=3)
        self.assertEqual(len(out.splitlines()), 3)


if __name__ == "__main__":
    unittest.main()
