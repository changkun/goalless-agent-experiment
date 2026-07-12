#!/usr/bin/env python3
"""
Conway's Game of Life — terminal edition.

Run:  python3 life.py
Keys: Ctrl-C to quit

Starts with a random soup and evolves it in your terminal.
"""

import os
import random
import time
import shutil

ALIVE = "█"
DEAD  = " "

def make_grid(rows, cols, density=0.3):
    return [[random.random() < density for c in range(cols)] for r in range(rows)]

def neighbours(grid, r, c, rows, cols):
    total = 0
    for dr in (-1, 0, 1):
        for dc in (-1, 0, 1):
            if dr == 0 and dc == 0:
                continue
            total += grid[(r + dr) % rows][(c + dc) % cols]
    return total

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
    lines = [f" Generation {generation}"]
    for row in grid:
        lines.append(" " + "".join(ALIVE if cell else DEAD for cell in row))
    return "\n".join(lines)

def main():
    term = shutil.get_terminal_size((80, 24))
    cols = term.columns - 2
    rows = term.lines - 3
    if cols < 10:
        cols = 40
    if rows < 5:
        rows = 20

    grid = make_grid(rows, cols)
    gen = 0

    try:
        while True:
            os.system("clear" if os.name != "nt" else "cls")
            print(render(grid, gen))
            time.sleep(0.12)
            grid = step(grid, rows, cols)
            gen += 1
    except KeyboardInterrupt:
        print(f"\n Stopped after {gen} generations. Thanks for watching!")

if __name__ == "__main__":
    main()
