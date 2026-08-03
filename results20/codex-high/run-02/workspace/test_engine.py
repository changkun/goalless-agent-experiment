import unittest

from gol import (
    Grid,
    blinker,
    glider,
    neighbors,
    next_generation,
    parse,
    render,
)


class TestNeighbors(unittest.TestCase):
    def test_returns_eight_cells(self):
        result = set(neighbors((2, 3)))
        expected = {
            (1, 2), (1, 3), (1, 4),
            (2, 2),         (2, 4),
            (3, 2), (3, 3), (3, 4),
        }
        self.assertEqual(result, expected)


class TestBlinker(unittest.TestCase):
    def test_period_two(self):
        g = blinker()  # {(0,0),(0,1),(0,2)} horizontal
        g2 = next_generation(g)
        g3 = next_generation(g2)
        self.assertEqual(g2, {(-1, 1), (0, 1), (1, 1)})  # vertical
        self.assertEqual(g, g3)  # back to original shape


class TestGlider(unittest.TestCase):
    def test_keeps_shape_after_full_cycle(self):
        g = glider()
        reference = glider()
        for _ in range(4):
            g = next_generation(g)
            reference = next_generation(reference)
        self.assertEqual(g, reference)

    def test_translates_diagonally(self):
        g = glider()
        box = self._box(g)
        for _ in range(8):
            g = next_generation(g)
        box2 = self._box(g)
        self.assertEqual((box2[0] - box[0], box2[1] - box[1]), (2, 2))

    @staticmethod
    def _box(grid):
        rows = [r for r, _ in grid]
        cols = [c for _, c in grid]
        return (min(rows), min(cols))


class TestParseRender(unittest.TestCase):
    def test_roundtrip(self):
        text = ".#.\n..#\n###\n"
        grid = parse(text)
        self.assertEqual(render(grid), text)


class TestGrid(unittest.TestCase):
    def test_isolated_cell_dies(self):
        g: Grid = {(0, 0)}
        self.assertEqual(next_generation(g), set())

    def test_block_is_still_life(self):
        block = parse("##\n##")
        self.assertEqual(next_generation(block), block)


if __name__ == "__main__":
    unittest.main()
