#!/usr/bin/env python3
"""Conway's Game of Life in the terminal."""

import os, time, random, sys

ROWS, COLS = 24, 60

def make_grid():
    return [[random.random() < 0.3 for _ in range(COLS)] for _ in range(ROWS)]

def neighbors(grid, r, c):
    count = 0
    for dr in (-1, 0, 1):
        for dc in (-1, 0, 1):
            if dr == 0 and dc == 0:
                continue
            nr, nc = (r + dr) % ROWS, (c + dc) % COLS
            count += grid[nr][nc]
    return count

def step(grid):
    new = [[False] * COLS for _ in range(ROWS)]
    for r in range(ROWS):
        for c in range(COLS):
            n = neighbors(grid, r, c)
            if grid[r][c]:
                new[r][c] = n in (2, 3)
            else:
                new[r][c] = n == 3
    return new

def render(grid, gen):
    lines = [f" Generation {gen}  |  alive: {sum(sum(row) for row in grid)}"]
    lines.append("+" + "-" * COLS + "+")
    for row in grid:
        lines.append("|" + "".join("█" if c else " " for c in row) + "|")
    lines.append("+" + "-" * COLS + "+")
    lines.append(" Press Ctrl+C to stop")
    return "\n".join(lines)

def main():
    grid = make_grid()
    gen = 0
    try:
        while True:
            os.system("clear" if os.name != "nt" else "cls")
            print(render(grid, gen))
            grid = step(grid)
            gen += 1
            time.sleep(0.15)
    except KeyboardInterrupt:
        print(f"\nStopped after {gen} generations.")

if __name__ == "__main__":
    main()
