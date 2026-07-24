"""Tests for grid model, generators, searches, renderer and CLI."""

from __future__ import annotations

import contextlib
import io
import unittest

from pathviz.cli import main, stats_table, summary
from pathviz.grid import Grid
from pathviz.mazes import GENERATORS, generate
from pathviz.render import PATH_GLYPH, frames, render
from pathviz.search import ALGORITHMS, search


def open_grid(width: int = 5, height: int = 5) -> Grid:
    grid = Grid(width, height)
    for y in range(height):
        for x in range(width):
            grid.carve((x, y))
    grid.start = (0, 0)
    grid.goal = (width - 1, height - 1)
    return grid


class GridTest(unittest.TestCase):
    def test_rejects_bad_dimensions(self):
        with self.assertRaises(ValueError):
            Grid(0, 4)

    def test_rejects_mismatched_cells(self):
        with self.assertRaises(ValueError):
            Grid(3, 2, cells=[[1, 1, 1]])

    def test_walls_are_not_neighbors(self):
        grid = Grid(3, 3)
        grid.carve((1, 1))
        grid.carve((1, 0))
        self.assertEqual(grid.neighbors((1, 1)), [(1, 0)])

    def test_weight_must_be_positive(self):
        grid = open_grid(3, 3)
        with self.assertRaises(ValueError):
            grid.set_weight((1, 1), 0)

    def test_path_cost_excludes_start(self):
        grid = open_grid(3, 1)
        grid.set_weight((1, 0), 4)
        grid.set_weight((0, 0), 9)
        self.assertEqual(grid.path_cost([(0, 0), (1, 0), (2, 0)]), 5)

    def test_floors_lists_only_carved_cells(self):
        grid = Grid(2, 2)
        grid.carve((0, 1))
        self.assertEqual(list(grid.floors()), [(0, 1)])


class MazeTest(unittest.TestCase):
    def test_dimensions_forced_odd_and_minimum(self):
        grid = generate(10, 2, seed=1)
        self.assertEqual((grid.width, grid.height), (9, 3))

    def test_seed_is_deterministic(self):
        a = generate(21, 11, seed=42, weighted=True)
        b = generate(21, 11, seed=42, weighted=True)
        self.assertEqual(a.cells, b.cells)
        self.assertEqual(a.weights, b.weights)

    def test_unknown_generator_rejected(self):
        with self.assertRaises(ValueError):
            generate(9, 9, kind="spiral")

    def test_every_generator_is_solvable(self):
        for kind in GENERATORS:
            for seed in range(4):
                grid = generate(21, 11, kind=kind, seed=seed)
                with self.subTest(kind=kind, seed=seed):
                    self.assertTrue(search(grid, "bfs").found)

    def test_border_stays_walled(self):
        grid = generate(15, 9, seed=5)
        for x in range(grid.width):
            self.assertFalse(grid.is_floor((x, 0)))
            self.assertFalse(grid.is_floor((x, grid.height - 1)))
        for y in range(grid.height):
            self.assertFalse(grid.is_floor((0, y)))
            self.assertFalse(grid.is_floor((grid.width - 1, y)))

    def test_weighted_grids_have_costly_terrain(self):
        grid = generate(31, 21, seed=3, weighted=True)
        self.assertGreater(max(grid.weight(c) for c in grid.floors()), 1)


class SearchTest(unittest.TestCase):
    def test_unknown_algorithm_rejected(self):
        with self.assertRaises(ValueError):
            search(open_grid(), "greedy")

    def test_wall_endpoints_rejected(self):
        grid = Grid(3, 3)
        with self.assertRaises(ValueError):
            search(grid, "bfs")

    def test_path_is_contiguous_and_anchored(self):
        grid = generate(21, 11, seed=9, weighted=True)
        for algo in ALGORITHMS:
            result = search(grid, algo)
            with self.subTest(algo=algo):
                self.assertEqual(result.path[0], grid.start)
                self.assertEqual(result.path[-1], grid.goal)
                for a, b in zip(result.path, result.path[1:]):
                    self.assertEqual(abs(a[0] - b[0]) + abs(a[1] - b[1]), 1)
                self.assertEqual(result.cost, grid.path_cost(result.path))

    def test_bfs_is_shortest_in_steps(self):
        grid = open_grid(6, 4)
        result = search(grid, "bfs")
        self.assertEqual(len(result.path), 9)

    def test_dijkstra_beats_bfs_on_weighted_detour(self):
        grid = open_grid(5, 3)
        for y in range(3):
            grid.set_weight((2, y), 9 if y == 0 else 1)
        grid.goal = (4, 0)
        bfs = search(grid, "bfs")
        dijkstra = search(grid, "dijkstra")
        self.assertLess(dijkstra.cost, bfs.cost)

    def test_astar_matches_dijkstra_cost_but_expands_no_more(self):
        grid = generate(31, 21, seed=11, weighted=True)
        dijkstra = search(grid, "dijkstra")
        astar = search(grid, "astar")
        self.assertEqual(astar.cost, dijkstra.cost)
        self.assertLessEqual(astar.expanded, dijkstra.expanded)

    def test_unreachable_goal_reports_no_path(self):
        grid = Grid(3, 1)
        grid.carve((0, 0))
        grid.carve((2, 0))
        grid.start, grid.goal = (0, 0), (2, 0)
        result = search(grid, "bfs")
        self.assertFalse(result.found)
        self.assertEqual(result.path, [])

    def test_visited_cells_are_unique_and_start_first(self):
        grid = generate(21, 11, seed=4)
        for algo in ALGORITHMS:
            result = search(grid, algo)
            with self.subTest(algo=algo):
                self.assertEqual(result.visited[0], grid.start)
                self.assertEqual(len(result.visited), len(set(result.visited)))


class RenderTest(unittest.TestCase):
    def test_dimensions_match_grid(self):
        grid = generate(15, 9, seed=2)
        lines = render(grid).splitlines()
        self.assertEqual(len(lines), grid.height)
        self.assertTrue(all(len(line) == grid.width for line in lines))

    def test_terrain_tiers_use_distinct_glyphs(self):
        grid = open_grid(4, 1)
        grid.set_weight((1, 0), 2)
        grid.set_weight((2, 0), 7)
        self.assertEqual(render(grid), "S,;G")

    def test_path_overrides_visited(self):
        grid = open_grid(3, 1)
        text = render(grid, visited={(1, 0)}, path=[(0, 0), (1, 0), (2, 0)])
        self.assertEqual(text[1], PATH_GLYPH)

    def test_color_wraps_glyphs_in_escapes(self):
        grid = open_grid(3, 1)
        self.assertIn("\033[", render(grid, color=True))

    def test_frames_end_with_final_path_frame(self):
        grid = generate(15, 9, seed=6)
        result = search(grid, "bfs")
        sequence = frames(grid, result, step=3)
        self.assertIn(PATH_GLYPH, sequence[-1].text)
        self.assertEqual(sequence[-1].frontier, 0)
        self.assertLess(len(sequence), result.expanded + 1)

    def test_frames_rejects_bad_step(self):
        grid = open_grid()
        with self.assertRaises(ValueError):
            frames(grid, search(grid, "bfs"), step=0)


class CliTest(unittest.TestCase):
    def run_cli(self, argv: list[str]) -> tuple[int, str]:
        buffer = io.StringIO()
        with contextlib.redirect_stdout(buffer):
            code = main(argv)
        return code, buffer.getvalue()

    def test_single_run_prints_grid_and_summary(self):
        code, out = self.run_cli(["--width", "15", "--height", "9", "--seed", "1", "--no-color"])
        self.assertEqual(code, 0)
        self.assertIn("astar: path", out)
        self.assertIn(PATH_GLYPH, out)

    def test_compare_mode_lists_all_algorithms(self):
        code, out = self.run_cli(["--width", "15", "--height", "9", "--compare", "--no-color"])
        self.assertEqual(code, 0)
        for algo in ALGORITHMS:
            self.assertIn(algo, out)

    def test_animation_emits_multiple_frames(self):
        code, out = self.run_cli(
            ["--width", "15", "--height", "9", "--animate", "--fps", "0", "--step", "5",
             "--no-color"]
        )
        self.assertEqual(code, 0)
        self.assertGreater(out.count("frontier"), 1)

    def test_summary_reports_failure(self):
        grid = Grid(3, 1)
        grid.carve((0, 0))
        grid.carve((2, 0))
        grid.start, grid.goal = (0, 0), (2, 0)
        self.assertIn("no path", summary(search(grid, "bfs")))

    def test_stats_table_is_aligned(self):
        grid = generate(15, 9, seed=8, weighted=True)
        table = stats_table([search(grid, algo) for algo in ALGORITHMS])
        lines = table.splitlines()
        self.assertEqual(len(lines), len(ALGORITHMS) + 2)
        self.assertTrue(all(set(lines[1]) <= {"-", " "} for _ in lines[1:2]))
        columns = {line.index(line.split()[1]) for line in [lines[0], *lines[2:]]}
        self.assertEqual(len(columns), 1)


if __name__ == "__main__":
    unittest.main()
