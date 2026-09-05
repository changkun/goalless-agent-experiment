#!/usr/bin/env python3
"""Generate a random maze, solve it, and draw both in the terminal.

Usage:
    python3 maze.py [width] [height] [seed]

Defaults to a 21x11 maze with a random seed.
"""

import random
import sys
from collections import deque

WALL = "█"
OPEN = " "
PATH = "·"


def generate(width, height, rng):
    """Carve a maze with recursive backtracking on a (2w+1)x(2h+1) grid."""
    grid = [[WALL] * (2 * width + 1) for _ in range(2 * height + 1)]
    stack = [(0, 0)]
    visited = {(0, 0)}
    grid[1][1] = OPEN
    while stack:
        x, y = stack[-1]
        neighbors = [
            (nx, ny)
            for nx, ny in ((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1))
            if 0 <= nx < width and 0 <= ny < height and (nx, ny) not in visited
        ]
        if not neighbors:
            stack.pop()
            continue
        nx, ny = rng.choice(neighbors)
        grid[y + ny + 1][x + nx + 1] = OPEN
        grid[2 * ny + 1][2 * nx + 1] = OPEN
        visited.add((nx, ny))
        stack.append((nx, ny))
    return grid


def solve(grid):
    """Breadth-first search from top-left cell to bottom-right cell."""
    rows, cols = len(grid), len(grid[0])
    start, goal = (1, 1), (rows - 2, cols - 2)
    parents = {start: None}
    queue = deque([start])
    while queue:
        r, c = queue.popleft()
        if (r, c) == goal:
            break
        for nr, nc in ((r + 1, c), (r - 1, c), (r, c + 1), (r, c - 1)):
            if grid[nr][nc] == OPEN and (nr, nc) not in parents:
                parents[(nr, nc)] = (r, c)
                queue.append((nr, nc))
    path, node = [], goal
    while node is not None:
        path.append(node)
        node = parents[node]
    return path


def render(grid, path):
    for r, c in path:
        grid[r][c] = PATH
    grid[1][0] = PATH   # entrance
    grid[-2][-1] = PATH  # exit
    return "\n".join("".join(row) for row in grid)


def main(argv):
    width = int(argv[1]) if len(argv) > 1 else 21
    height = int(argv[2]) if len(argv) > 2 else 11
    seed = int(argv[3]) if len(argv) > 3 else random.randrange(10**6)
    rng = random.Random(seed)
    grid = generate(width, height, rng)
    path = solve(grid)
    print(render(grid, path))
    print(f"\n{width}x{height} maze, seed={seed}, solution length={len(path)}")


if __name__ == "__main__":
    main(sys.argv)
