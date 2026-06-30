#!/usr/bin/env python3
"""Conway's Game of Life, animated in the terminal."""
import os
import sys
import time

WIDTH, HEIGHT = 60, 30

GLIDER_GUN = [
    (1, 5), (1, 6), (2, 5), (2, 6),
    (11, 5), (11, 6), (11, 7),
    (12, 4), (12, 8),
    (13, 3), (13, 9),
    (14, 3), (14, 9),
    (15, 6),
    (16, 4), (16, 8),
    (17, 5), (17, 6), (17, 7),
    (18, 6),
    (21, 3), (21, 4), (21, 5),
    (22, 3), (22, 4), (22, 5),
    (23, 2), (23, 6),
    (25, 1), (25, 2), (25, 6), (25, 7),
    (35, 3), (35, 4), (36, 3), (36, 4),
]


def make_grid():
    grid = [[0] * WIDTH for _ in range(HEIGHT)]
    for x, y in GLIDER_GUN:
        if 0 <= y < HEIGHT and 0 <= x < WIDTH:
            grid[y][x] = 1
    return grid


def step(grid):
    new = [[0] * WIDTH for _ in range(HEIGHT)]
    for y in range(HEIGHT):
        for x in range(WIDTH):
            n = sum(
                grid[(y + dy) % HEIGHT][(x + dx) % WIDTH]
                for dy in (-1, 0, 1) for dx in (-1, 0, 1)
                if not (dx == 0 and dy == 0)
            )
            if grid[y][x]:
                new[y][x] = 1 if n in (2, 3) else 0
            else:
                new[y][x] = 1 if n == 3 else 0
    return new


def render(grid, gen):
    lines = [f"Conway's Game of Life — generation {gen}  (Ctrl+C to quit)"]
    for row in grid:
        lines.append("".join("█" if c else " " for c in row))
    sys.stdout.write("\x1b[H\x1b[2J" + "\n".join(lines) + "\n")
    sys.stdout.flush()


def main():
    grid = make_grid()
    gen = 0
    try:
        while True:
            render(grid, gen)
            grid = step(grid)
            gen += 1
            time.sleep(0.08)
    except KeyboardInterrupt:
        print("\nBye!")


if __name__ == "__main__":
    main()
