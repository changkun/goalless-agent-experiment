import random
import unittest

from maze import Maze, generate, render, solve


class MazeTests(unittest.TestCase):
    def test_generated_maze_is_perfect(self):
        # A perfect maze on W*H cells is a spanning tree: exactly W*H - 1 openings.
        for seed in range(20):
            maze = generate(7, 5, random.Random(seed))
            openings = sum(4 - len(w) for w in maze.walls.values()) // 2
            self.assertEqual(openings, 7 * 5 - 1)

    def test_every_cell_is_reachable(self):
        maze = generate(12, 9, random.Random(1))
        for y in range(maze.height):
            for x in range(maze.width):
                self.assertTrue(solve(maze, (0, 0), (x, y)), f"unreachable {(x, y)}")

    def test_path_is_contiguous_and_respects_walls(self):
        maze = generate(15, 15, random.Random(42))
        path = solve(maze)
        self.assertEqual(path[0], (0, 0))
        self.assertEqual(path[-1], (14, 14))
        for a, b in zip(path, path[1:]):
            self.assertIn(b, list(maze.neighbors(*a)))

    def test_unsolvable_returns_empty(self):
        maze = Maze(2, 1)  # all walls intact
        self.assertEqual(solve(maze), [])

    def test_render_dimensions(self):
        maze = generate(4, 3, random.Random(0))
        lines = render(maze, solve(maze)).splitlines()
        self.assertEqual(len(lines), 2 * 3 + 1)
        self.assertTrue(all(len(line) == 4 * 4 + 1 for line in lines))

    def test_seed_is_deterministic(self):
        a = render(generate(6, 6, random.Random(7)))
        b = render(generate(6, 6, random.Random(7)))
        self.assertEqual(a, b)

    def test_rejects_bad_dimensions(self):
        with self.assertRaises(ValueError):
            Maze(0, 3)


if __name__ == "__main__":
    unittest.main()
