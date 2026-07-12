#!/usr/bin/env python3
"""Conway's Game of Life — terminal edition.

Run:  python3 life.py
Keys: Ctrl-C to quit

Starts with a random soup and evolves in place using ANSI escape codes.
"""

import os
import random
import time

ALIVE = "█"
DEAD = " "
DELAY = 0.08

def make_grid(rows, cols, density=0.35):
    return [[random.random() < density for _ in range(cols)] for _ in range(rows)]

def neighbours(grid, r, c, rows, cols):
    count = 0
    for dr in (-1, 0, 1):
        for dc in (-1, 0, 1):
            if dr == 0 and dc == 0:
                continue
            nr, nc = (r + dr) % rows, (c + dc) % cols
            count += grid[nr][nc]
    return count

def step(grid, rows, cols):
    new = [[False] * cols for _ in range(rows)]
    for r in range(rows):
        for c in range(cols):
            n = neighbours(grid, r, c, rows, cols)
            if grid[r][c]:
                new[r][c] = n in (2, 3)
            else:
                new[r][c] = n == 3
    return new

def render(grid, generation):
    lines = [f"\033[1;36m Game of Life \033[0m  gen {generation}"]
    for row in grid:
        lines.append("".join(ALIVE if cell else DEAD for cell in row))
    return "\n".join(lines)

def main():
    try:
        size = os.get_terminal_size()
        cols = size.columns - 1
        rows = size.lines - 3
    except OSError:
        cols, rows = 60, 24

    cols = max(cols, 10)
    rows = max(rows, 10)

    grid = make_grid(rows, cols)
    gen = 0

    print("\033[2J\033[H", end="")  # clear screen

    try:
        while True:
            print(f"\033[H{render(grid, gen)}", end="", flush=True)
            grid = step(grid, rows, cols)
            gen += 1
            time.sleep(DELAY)
    except KeyboardInterrupt:
        print(f"\n\033[0mStopped after {gen} generations. 👋")

if __name__ == "__main__":
    main()
