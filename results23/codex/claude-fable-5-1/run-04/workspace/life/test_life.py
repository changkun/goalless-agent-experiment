import unittest

from life import PATTERNS, parse_pattern, step


class LifeRules(unittest.TestCase):
    def test_blinker_oscillates_with_period_two(self):
        blinker = {(1, 0), (1, 1), (1, 2)}
        after_one = step(blinker, 5, 5)
        self.assertEqual(after_one, {(0, 1), (1, 1), (2, 1)})
        self.assertEqual(step(after_one, 5, 5), blinker)

    def test_block_is_still_life(self):
        block = {(1, 1), (2, 1), (1, 2), (2, 2)}
        self.assertEqual(step(block, 6, 6), block)

    def test_lonely_cell_dies(self):
        self.assertEqual(step({(2, 2)}, 5, 5), set())

    def test_glider_translates_after_four_generations(self):
        glider = parse_pattern(PATTERNS["glider"], 20, 20)
        cells = glider
        for _ in range(4):
            cells = step(cells, 20, 20)
        self.assertEqual(cells, {(x + 1, y + 1) for x, y in glider})

    def test_grid_wraps_around_edges(self):
        blinker_on_edge = {(0, 0), (0, 1), (0, 4)}  # vertical blinker wrapping top/bottom
        self.assertEqual(step(blinker_on_edge, 5, 5), {(4, 0), (0, 0), (1, 0)})


if __name__ == "__main__":
    unittest.main()
