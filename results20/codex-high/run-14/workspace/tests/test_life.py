import sys
import unittest

sys.path.insert(0, ".")

from life.engine import Game, next_generation, parse_pattern, render


class TestNextGeneration(unittest.TestCase):
    def test_block_is_stable(self):
        block = {(0, 0), (0, 1), (1, 0), (1, 1)}
        self.assertEqual(next_generation(block), block)

    def test_blinker_oscillates(self):
        vertical = {(1, 0), (1, 1), (1, 2)}
        horizontal = {(0, 1), (1, 1), (2, 1)}
        self.assertEqual(next_generation(vertical), horizontal)
        self.assertEqual(next_generation(horizontal), vertical)

    def test_glider_moves(self):
        glider = {(0, 1), (1, 2), (2, 0), (2, 1), (2, 2)}
        next_g = next_generation(glider)
        self.assertEqual(next_g, {(1, 0), (1, 2), (2, 1), (2, 2), (3, 1)})

    def test_lonely_cell_dies(self):
        self.assertEqual(next_generation({(0, 0)}), set())


class TestParseAndRender(unittest.TestCase):
    def test_parse_pattern(self):
        cells = parse_pattern("O..\n.O.\n..O")
        self.assertEqual(cells, {(0, 0), (1, 1), (2, 2)})

    def test_render_clips_bounding_box(self):
        rendered = render({(5, 5), (5, 6)})
        self.assertEqual(rendered, "oo")

    def test_render_empty(self):
        self.assertEqual(render(set()), "")


class TestGame(unittest.TestCase):
    def test_load_centers_pattern(self):
        game = Game(8, 8)
        game.load("block")
        self.assertEqual(game.population(), 4)
        self.assertIn((3, 3), game.live)

    def test_board_dimensions(self):
        game = Game(3, 2)
        game.load("blinker")
        self.assertEqual(len(game.board().splitlines()), 2)

    def test_generation_counter(self):
        game = Game(5, 5, wrap=True)
        game.load("blinker")
        game.step()
        self.assertEqual(game.generation, 1)


if __name__ == "__main__":
    unittest.main()
