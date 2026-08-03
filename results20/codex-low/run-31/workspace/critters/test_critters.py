import unittest

from critters import PRESETS, RULES, field, random_grid, render_ansi, render_blocks, stamp, step


class RuleTests(unittest.TestCase):
    def test_presets_and_rules_exist(self):
        self.assertIn("life", RULES)
        self.assertIn("glider-gun", PRESETS)
        self.assertGreaterEqual(len(RULES), 4)

    def test_all_presets_build_valid_grids(self):
        for name, spec in PRESETS.items():
            grid = spec["make"](40, 30)
            self.assertEqual(len(grid), 30)
            self.assertTrue(all(len(row) == 40 for row in grid))
            self.assertTrue(all(c in (0, 1) for row in grid for c in row))

    def test_all_rules_preserve_shape(self):
        grid = PRESETS["random"]["make"](25, 20)
        for name in RULES:
            out = step(grid, name)
            self.assertEqual(len(out), 20, name)
            self.assertTrue(all(len(r) == 25 for r in out), name)
            self.assertTrue(all(c in (0, 1) for r in out for c in r), name)

    def test_still_life_under_life(self):
        block = [(0, 0), (1, 0), (0, 1), (1, 1)]
        grid = stamp(10, 10, block)
        out = step(grid, "life")
        self.assertEqual(out, grid)

    def test_seeds_die_without_partners(self):
        grid = [[0] * 6 for _ in range(6)]
        grid[2][2] = 1  # isolated cell: no births, dies
        out = step(grid, "seeds")
        self.assertEqual(sum(map(sum, out)), 0)

    def test_glider_moves_diagonally(self):
        glider = [(0, 1), (1, 2), (2, 0), (2, 1), (2, 2)]
        a = stamp(12, 12, glider)
        b = stamp(12, 12, glider)
        for _ in range(4):
            a = step(a, "life")
            b = step(b, "life")
        # The glider should have translated 1 cell down-right from its start.
        self.assertEqual(b, a)

    def test_field_tiles_pattern(self):
        grid = field(24, 24, [(0, 0), (1, 0)])
        alive = [(x, y) for y in range(24) for x in range(24) if grid[y][x]]
        self.assertGreater(len(alive), 2)


class RenderTests(unittest.TestCase):
    def test_render_blocks_halfs_height(self):
        grid = [[1] * 8 for _ in range(8)]
        rows = render_blocks(grid)
        self.assertEqual(len(rows), 4)
        self.assertTrue(all(len(r) == 4 for r in rows))
        self.assertTrue(all(ch == "\u2588" for r in rows for ch in r))

    def test_render_ansi_uses_colour_codes(self):
        grid = PRESETS["pulsar"]["make"](20, 20)
        out = render_ansi(grid)
        self.assertIn("\033[36;1m", out)
        self.assertIn("\033[0m", out)


class CliTests(unittest.TestCase):
    def test_list_exits_zero(self):
        from critters import main
        self.assertEqual(main(["--list"]), 0)

    def test_headless_runs_frames(self):
        from io import StringIO
        from unittest.mock import patch

        from critters import main

        with patch("sys.stdout", new_callable=StringIO) as fake_out:
            rc = main(["--frames", "3", "--preset", "glider", "--delay", "0.0"])
        self.assertEqual(rc, 0)
        out = fake_out.getvalue()
        self.assertIn("frame 0", out)
        self.assertIn("frame 2", out)


if __name__ == "__main__":
    unittest.main()
