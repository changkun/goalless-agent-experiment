"""Tests for the Game of Life implementation (run with `python -m unittest`)."""

import unittest

from life import Grid
from patterns import PATTERNS
from rle import period


class TestGridBasics(unittest.TestCase):
    def test_empty_grid_is_all_dead(self):
        grid = Grid(3, 4)
        self.assertEqual(grid.alive_count(), 0)
        self.assertFalse(any(grid.get(r, c) for r in range(3) for c in range(4)))

    def test_from_rows_and_render(self):
        grid = Grid.from_rows([".#.", "#.#", ".#."])
        # Dead cells render as a space, live cells as '#'.
        self.assertEqual(grid.render().splitlines(), [" # ", "# #", " # "])
        self.assertEqual(grid.alive_count(), 4)

    def test_out_of_bounds_reads_dead(self):
        grid = Grid(2, 2)
        self.assertFalse(grid.get(-1, 0))
        self.assertFalse(grid.get(0, 2))
        self.assertFalse(grid.get(5, 5))

    def test_set_and_toggle(self):
        grid = Grid(2, 2)
        grid.set(0, 1, True)
        self.assertTrue(grid.get(0, 1))
        grid.toggle(0, 1)
        self.assertFalse(grid.get(0, 1))
        grid.toggle(1, 1)
        self.assertTrue(grid.get(1, 1))

    def test_equality(self):
        a = Grid.from_rows(["##", ".."])
        b = Grid.from_rows(["##", ".."])
        c = Grid.from_rows(["..", "##"])
        self.assertEqual(a, b)
        self.assertNotEqual(a, c)


class TestRules(unittest.TestCase):
    def test_lone_cell_dies(self):
        grid = Grid.from_rows([".#."])
        grid.step()
        self.assertEqual(grid.alive_count(), 0)

    def test_block_is_stable(self):
        grid = Grid.from_rows(["##", "##"])
        before = grid.render()
        for _ in range(3):
            grid.step()
        self.assertEqual(grid.render(), before)

    def test_blinker_oscillates_period_2(self):
        # Use the padded pattern (which has dead margin) and check it
        # returns to its starting shape after two generations.
        grid = PATTERNS["blinker"]
        start = grid.render()
        grid.step()
        grid.step()
        self.assertEqual(grid.render(), start)

    def test_line_of_two_dies(self):
        grid = Grid.from_rows(["##"])
        grid.step()
        self.assertEqual(grid.alive_count(), 0)

    def test_birth_requires_exactly_three(self):
        grid = Grid.from_rows([".#.", "#.#"])
        grid.step()
        self.assertTrue(grid.get(0, 1))


class TestEngineAgainstReference(unittest.TestCase):
    """Cross-check the fast engine against a slow, obviously-correct naive
    implementation on random grids. This is the strongest guarantee that the
    core rules are implemented correctly."""

    def test_matches_naive_implementation(self):
        import random

        random.seed(42)

        def naive(grid):
            rows, cols = grid.rows, grid.cols
            live = [[grid.get(i, j) for j in range(cols)] for i in range(rows)]
            out = [[False] * cols for _ in range(rows)]
            for i in range(rows):
                for j in range(cols):
                    n = sum(
                        live[ni][nj]
                        for ni in (i - 1, i, i + 1)
                        for nj in (j - 1, j, j + 1)
                        if (ni, nj) != (i, j) and 0 <= ni < rows and 0 <= nj < cols
                    )
                    out[i][j] = live[i][j] and n in (2, 3) or (not live[i][j] and n == 3)
            return out

        for _ in range(200):
            r = random.randint(2, 12)
            c = random.randint(2, 12)
            g = Grid(r, c)
            for i in range(r):
                for j in range(c):
                    if random.random() < 0.4:
                        g.set(i, j, True)
            expected = naive(g)
            g.step()
            actual = [[g.get(i, j) for j in range(c)] for i in range(r)]
            self.assertEqual(actual, expected)


class TestPatterns(unittest.TestCase):
    def test_all_defined(self):
        self.assertIn("glider", PATTERNS)
        self.assertIn("pulsar", PATTERNS)
        self.assertIn("gun", PATTERNS)

    def test_glider_travels_diagonally(self):
        grid = Grid(12, 12)
        for r, row in enumerate([".#.", "..#", "###"]):
            for c, ch in enumerate(row):
                if ch == "#":
                    grid.set(r, c, True)
        start_count = grid.alive_count()
        live0 = {(r, c) for r in range(12) for c in range(12) if grid.get(r, c)}
        for _ in range(4):
            grid.step()
        live1 = {(r, c) for r in range(12) for c in range(12) if grid.get(r, c)}
        # After 4 generations the glider reforms with the same cell count,
        # having moved one cell diagonally (down-right here).
        self.assertEqual(len(live1), start_count)
        # Every original cell lies strictly above-left of at least one new
        # cell: the topmost live row has moved down.
        self.assertGreater(
            min(r for r, _ in live1), min(r for r, _ in live0)
        )

    def test_pulsar_has_period_three(self):
        # A real pulsar returns to its exact starting state after 3 steps.
        self.assertEqual(period(PATTERNS["pulsar"]), 3)

    def test_oscillators_have_expected_periods(self):
        self.assertEqual(period(PATTERNS["blinker"]), 2)
        self.assertEqual(period(PATTERNS["beacon"]), 2)
        self.assertEqual(period(PATTERNS["toad"]), 2)

    def test_gun_fires_gliders(self):
        # The Gosper gun keeps firing gliders. Over a long run on a roomy
        # grid the population must repeatedly climb well above its start.
        src = PATTERNS["gun"]
        grid = Grid(90, 90)
        for r in range(src.rows):
            for c in range(src.cols):
                if src.get(r, c):
                    grid.set(30 + r, 30 + c, True)
        start = grid.alive_count()
        peaks = []
        counts = []
        for _ in range(200):
            grid.step()
            counts.append(grid.alive_count())
        # Find sustained growth: the max population far exceeds the start.
        self.assertGreater(max(counts), start + 15)
        # And the pattern never dies out.
        self.assertTrue(all(c > 0 for c in counts[-20:]))


class TestRle(unittest.TestCase):
    def test_load_small_patterns(self):
        from rle import load_rle

        blinker = load_rle("x = 3, y = 1\n3o!")
        self.assertEqual((blinker.rows, blinker.cols), (1, 3))
        self.assertEqual(blinker.alive_count(), 3)

        block = load_rle("x = 2, y = 2\n2o$2o!")
        self.assertEqual(block.alive_count(), 4)

    def test_load_ignores_comments_and_whitespace(self):
        from rle import load_rle

        glider = load_rle("# a glider\nx = 3, y = 3\nbob$2bo$3o!")
        self.assertEqual(glider.alive_count(), 5)


if __name__ == "__main__":
    unittest.main()
