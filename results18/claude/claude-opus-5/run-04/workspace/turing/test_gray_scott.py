"""Tests: python3 -m unittest discover -s turing"""

from __future__ import annotations

import unittest

from turing.gray_scott import Grid, laplacian, seeded, simulate, step
from turing.render import squash, to_text


class TestLaplacian(unittest.TestCase):
    def test_constant_field_has_zero_laplacian(self):
        self.assertEqual(laplacian([3.0] * 12, 4), [0.0] * 12)

    def test_spike_matches_five_point_stencil(self):
        # A single unit spike in a 5x5 torus: -4 at the spike, +1 at each of
        # its four neighbours, 0 elsewhere.
        flat = [0.0] * 25
        flat[12] = 1.0  # row 2, col 2
        lap = laplacian(flat, 5)
        self.assertEqual(lap[12], -4.0)
        for neighbour in (7, 17, 11, 13):
            self.assertEqual(lap[neighbour], 1.0)
        self.assertEqual(sum(lap), 0.0)  # the stencil conserves total mass

    def test_horizontal_wrap_stays_within_its_row(self):
        # The left neighbour of (row 1, col 0) must be (row 1, col 3) -- not
        # the end of row 0, which is what shifting the flat list would give.
        flat = [0.0] * 12
        flat[4] = 1.0  # row 1, col 0
        lap = laplacian(flat, 4)
        self.assertEqual(lap[7], 1.0)  # row 1, col 3: wrapped within the row
        self.assertEqual(lap[3], 0.0)  # row 0, col 3: untouched

    def test_vertical_wrap(self):
        flat = [0.0] * 12
        flat[0] = 1.0  # row 0, col 0
        lap = laplacian(flat, 4)
        self.assertEqual(lap[8], 1.0)  # bottom row is the neighbour above


class TestDynamics(unittest.TestCase):
    def test_uniform_state_is_a_fixed_point(self):
        grid = Grid(6, 6, [1.0] * 36, [0.0] * 36)
        step(grid, feed=0.037, kill=0.065)
        self.assertEqual(grid.u, [1.0] * 36)
        self.assertEqual(grid.v, [0.0] * 36)

    def test_seed_is_reproducible_and_perturbs_the_dish(self):
        a = seeded(20, 20, seed=7)
        b = seeded(20, 20, seed=7)
        self.assertEqual(a.v, b.v)
        self.assertNotEqual(seeded(20, 20, seed=8).v, a.v)
        self.assertGreater(max(a.v), 0.0)

    def test_patterns_stay_bounded_and_nontrivial(self):
        grid = simulate(32, 32, preset="mitosis", steps=400, seed=1)
        self.assertTrue(all(-0.01 <= x <= 1.01 for x in grid.u))
        self.assertTrue(all(-0.01 <= x <= 1.01 for x in grid.v))
        # Structure has formed: V is neither dead nor uniform.
        self.assertGreater(max(grid.v) - min(grid.v), 0.05)

    def test_unknown_preset_rejected(self):
        with self.assertRaises(KeyError):
            simulate(8, 8, preset="nope", steps=1)


class TestRender(unittest.TestCase):
    def test_squash_averages_row_pairs(self):
        grid = Grid(2, 4, [0.0] * 8, [0.0, 1.0, 2.0, 3.0, 0.0, 0.0, 4.0, 4.0])
        field, w, rows = squash(grid, 2)
        self.assertEqual((w, rows), (2, 2))
        self.assertEqual(field, [1.0, 2.0, 2.0, 2.0])

    def test_text_shape_and_extremes(self):
        grid = Grid(4, 4, [0.0] * 16, [0.0] * 8 + [1.0] * 8)
        text = to_text(grid, ramp="ascii", factor=2)
        lines = text.splitlines()
        self.assertEqual(len(lines), 2)
        self.assertTrue(all(len(line) == 4 for line in lines))
        self.assertEqual(lines[0], "    ")  # min -> first ramp char
        self.assertEqual(lines[1], "@@@@")  # max -> last ramp char

    def test_flat_field_renders_blank(self):
        grid = Grid(3, 2, [0.0] * 6, [0.5] * 6)
        self.assertEqual(to_text(grid, factor=2), "   ")


if __name__ == "__main__":
    unittest.main()
