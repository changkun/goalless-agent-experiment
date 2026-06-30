#!/usr/bin/env python3
import os
import shutil
import sys
import time

GLIDER_GUN = [
    "........................O...........",
    "......................O.O...........",
    "............OO......OO............OO",
    "...........O...O....OO............OO",
    "OO........O.....O...OO..............",
    "OO........O...O.OO....O.O...........",
    "..........O.....O.......O...........",
    "...........O...O....................",
    "............OO.......................",
]

COLORS = ["\033[36m", "\033[35m", "\033[33m", "\033[32m", "\033[34m"]
RESET = "\033[0m"
HIDE_CURSOR = "\033[?25l"
SHOW_CURSOR = "\033[?25h"


def make_grid(width, height):
    grid = [[0] * width for _ in range(height)]
    for r, row in enumerate(GLIDER_GUN):
        for c, ch in enumerate(row):
            if ch == "O" and r + 2 < height and c + 2 < width:
                grid[r + 2][c + 2] = 1
    return grid


def step(grid):
    h, w = len(grid), len(grid[0])
    new = [[0] * w for _ in range(h)]
    for r in range(h):
        for c in range(w):
            n = 0
            for dr in (-1, 0, 1):
                for dc in (-1, 0, 1):
                    if dr == 0 and dc == 0:
                        continue
                    n += grid[(r + dr) % h][(c + dc) % w]
            if grid[r][c] and n in (2, 3):
                new[r][c] = grid[r][c] + 1
            elif not grid[r][c] and n == 3:
                new[r][c] = 1
    return new


def render(grid, generation):
    lines = [f" Conway's Game of Life — generation {generation}  (Ctrl+C to stop)"]
    for row in grid:
        line = []
        for cell in row:
            if cell == 0:
                line.append(" ")
            else:
                color = COLORS[min(cell, len(COLORS)) - 1]
                line.append(f"{color}@{RESET}")
        lines.append("".join(line))
    sys.stdout.write("\033[H" + "\n".join(lines) + "\n")
    sys.stdout.flush()


def main():
    size = shutil.get_terminal_size((80, 24))
    width, height = size.columns, max(size.lines - 2, 10)
    grid = make_grid(width, height)
    generation = 0
    sys.stdout.write(HIDE_CURSOR + "\033[2J")
    try:
        while True:
            render(grid, generation)
            grid = step(grid)
            generation += 1
            time.sleep(0.08)
    except KeyboardInterrupt:
        pass
    finally:
        sys.stdout.write(SHOW_CURSOR + "\n")
        sys.stdout.flush()
        print(f"Stopped after {generation} generations.")


if __name__ == "__main__":
    main()
