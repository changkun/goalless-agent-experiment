import io
import random
import unittest
from contextlib import redirect_stderr, redirect_stdout

from labyrinth import (
    GENERATORS,
    RENDERERS,
    Grid,
    braid,
    dead_ends,
    flood,
    is_perfect,
    longest_path,
    render_ascii,
    shortest_path,
    stats,
)
from labyrinth.cli import main
from labyrinth.grid import NORTH, SOUTH


class GridTest(unittest.TestCase):
    def test_dimensions_and_cells(self):
        grid = Grid(2, 3)
        self.assertEqual(len(grid), 6)
        self.assertEqual(
            list(grid.cells()), [(0, 0), (0, 1), (0, 2), (1, 0), (1, 1), (1, 2)]
        )

    def test_rejects_empty_grid(self):
        with self.assertRaises(ValueError):
            Grid(0, 5)

    def test_neighbors_clipped_to_bounds(self):
        grid = Grid(3, 3)
        self.assertEqual(sorted(grid.neighbors((0, 0))), [(0, 1), (1, 0)])
        self.assertEqual(len(grid.neighbors((1, 1))), 4)

    def test_link_is_symmetric_and_unlinkable(self):
        grid = Grid(2, 2)
        grid.link((0, 0), (0, 1))
        self.assertTrue(grid.linked((0, 1), (0, 0)))
        grid.unlink((0, 1), (0, 0))
        self.assertFalse(grid.linked((0, 0), (0, 1)))

    def test_link_rejects_non_adjacent(self):
        grid = Grid(3, 3)
        with self.assertRaises(ValueError):
            grid.link((0, 0), (2, 2))

    def test_edges_are_reported_once(self):
        grid = Grid(1, 3)
        grid.link((0, 0), (0, 1))
        grid.link((0, 2), (0, 1))
        self.assertEqual(list(grid.edges()), [((0, 0), (0, 1)), ((0, 1), (0, 2))])

    def test_walls_at_border_and_after_carving(self):
        grid = Grid(2, 1)
        self.assertTrue(grid.has_wall((0, 0), NORTH))
        self.assertTrue(grid.has_wall((0, 0), SOUTH))
        grid.link((0, 0), (1, 0))
        self.assertFalse(grid.has_wall((0, 0), SOUTH))


class GeneratorTest(unittest.TestCase):
    def test_every_algorithm_makes_a_perfect_maze(self):
        for name, generate in GENERATORS.items():
            with self.subTest(algorithm=name):
                grid = generate(8, 11, random.Random(7))
                self.assertTrue(is_perfect(grid))

    def test_seed_is_reproducible_and_seeds_differ(self):
        first = render_ascii(GENERATORS["prim"](6, 6, random.Random(3)))
        same = render_ascii(GENERATORS["prim"](6, 6, random.Random(3)))
        other = render_ascii(GENERATORS["prim"](6, 6, random.Random(4)))
        self.assertEqual(first, same)
        self.assertNotEqual(first, other)

    def test_binary_tree_top_row_is_one_corridor(self):
        grid = GENERATORS["binary"](5, 5, random.Random(1))
        for col in range(4):
            self.assertTrue(grid.linked((0, col), (0, col + 1)))

    def test_single_cell_maze_has_no_passages(self):
        for generate in GENERATORS.values():
            grid = generate(1, 1, random.Random(0))
            self.assertEqual(list(grid.edges()), [])

    def test_braiding_removes_dead_ends_and_adds_loops(self):
        grid = GENERATORS["backtracker"](10, 10, random.Random(5))
        before = len(dead_ends(grid))
        self.assertGreater(before, 0)
        braid(grid, random.Random(5))
        self.assertEqual(dead_ends(grid), [])
        self.assertFalse(is_perfect(grid))

    def test_partial_braid_keeps_some_dead_ends(self):
        grid = GENERATORS["kruskal"](12, 12, random.Random(11))
        before = len(dead_ends(grid))
        braid(grid, random.Random(11), ratio=0.5)
        after = len(dead_ends(grid))
        self.assertLess(after, before)
        self.assertGreater(after, 0)

    def test_braid_ratio_is_validated(self):
        with self.assertRaises(ValueError):
            braid(Grid(2, 2), ratio=1.5)


class SolverTest(unittest.TestCase):
    def setUp(self):
        self.grid = GENERATORS["backtracker"](9, 9, random.Random(42))

    def test_flood_reaches_every_cell(self):
        distances = flood(self.grid, (0, 0))
        self.assertEqual(len(distances), len(self.grid))
        self.assertEqual(distances[(0, 0)], 0)

    def test_flood_rejects_outside_cell(self):
        with self.assertRaises(ValueError):
            flood(self.grid, (99, 0))

    def test_shortest_path_is_a_valid_walk(self):
        path = shortest_path(self.grid, (0, 0), (8, 8))
        self.assertEqual(path[0], (0, 0))
        self.assertEqual(path[-1], (8, 8))
        self.assertEqual(len(set(path)), len(path))
        for a, b in zip(path, path[1:]):
            self.assertTrue(self.grid.linked(a, b))

    def test_shortest_path_matches_bfs_distance(self):
        distances = flood(self.grid, (0, 0))
        path = shortest_path(self.grid, (0, 0), (8, 8))
        self.assertEqual(len(path) - 1, distances[(8, 8)])

    def test_trivial_and_unreachable_paths(self):
        self.assertEqual(shortest_path(self.grid, (2, 2), (2, 2)), [(2, 2)])
        self.assertEqual(shortest_path(Grid(2, 2), (0, 0), (1, 1)), [])

    def test_longest_path_is_the_diameter(self):
        path = longest_path(self.grid)
        distances = flood(self.grid, path[0])
        self.assertEqual(len(path) - 1, max(distances.values()))

    def test_stats_report(self):
        report = stats(self.grid)
        self.assertEqual(report["cells"], 81)
        self.assertEqual(report["passages"], 80)
        self.assertTrue(report["perfect"])
        self.assertEqual(report["diameter"], len(longest_path(self.grid)))


class RenderTest(unittest.TestCase):
    def test_ascii_render_of_known_maze(self):
        grid = Grid(2, 2)
        grid.link((0, 0), (0, 1))
        grid.link((0, 1), (1, 1))
        grid.link((1, 1), (1, 0))
        self.assertEqual(
            render_ascii(grid),
            "\n".join(
                [
                    "+---+---+",
                    "|       |",
                    "+---+   +",
                    "|       |",
                    "+---+---+",
                ]
            ),
        )

    def test_ascii_render_marks_path(self):
        grid = Grid(1, 2)
        grid.link((0, 0), (0, 1))
        self.assertIn("*", render_ascii(grid, [(0, 0), (0, 1)]))

    def test_every_renderer_produces_a_rectangleish_block(self):
        grid = GENERATORS["prim"](5, 7, random.Random(9))
        for name, render in RENDERERS.items():
            with self.subTest(renderer=name):
                lines = render(grid).splitlines()
                self.assertEqual(len(lines), 2 * grid.height + 1)
                self.assertTrue(all(lines))

    def test_renderers_accept_a_solution_path(self):
        grid = GENERATORS["kruskal"](6, 6, random.Random(2))
        path = longest_path(grid)
        for name, render in RENDERERS.items():
            with self.subTest(renderer=name):
                plain = render(grid)
                marked = render(grid, path)
                self.assertNotEqual(plain, marked)


class CliTest(unittest.TestCase):
    def run_cli(self, *argv):
        out, err = io.StringIO(), io.StringIO()
        with redirect_stdout(out), redirect_stderr(err):
            code = main(list(argv))
        return code, out.getvalue(), err.getvalue()

    def test_default_run_prints_a_maze(self):
        code, out, _ = self.run_cli("-H", "4", "-W", "4", "-s", "1")
        self.assertEqual(code, 0)
        self.assertEqual(len(out.splitlines()), 9)

    def test_seed_makes_output_deterministic(self):
        first = self.run_cli("-H", "5", "-W", "5", "-s", "8", "-r", "ascii")
        second = self.run_cli("-H", "5", "-W", "5", "-s", "8", "-r", "ascii")
        self.assertEqual(first, second)

    def test_solve_and_longest_mark_a_trail(self):
        for flag in ("--solve", "--longest"):
            with self.subTest(flag=flag):
                _, out, _ = self.run_cli("-H", "5", "-W", "5", "-s", "2", "-r", "ascii", flag)
                self.assertIn("*", out)

    def test_stats_flag_prints_metrics(self):
        _, out, _ = self.run_cli("-H", "4", "-W", "4", "-s", "3", "--stats")
        self.assertIn("dead ends", out)
        self.assertIn("diameter", out)

    def test_braid_flag_opens_the_maze(self):
        _, plain, _ = self.run_cli("-H", "8", "-W", "8", "-s", "6", "-r", "ascii")
        _, braided, _ = self.run_cli("-H", "8", "-W", "8", "-s", "6", "-r", "ascii", "--braid", "1")
        self.assertNotEqual(plain, braided)

    def test_bad_arguments_are_rejected(self):
        for argv in (("-H", "0"), ("--braid", "2")):
            with self.subTest(argv=argv):
                code, _, err = self.run_cli(*argv)
                self.assertEqual(code, 2)
                self.assertTrue(err)


if __name__ == "__main__":
    unittest.main()
