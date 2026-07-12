#!/usr/bin/env python3
"""Conway's Game of Life — terminal edition with color and animation."""

import os
import sys
import time
import random
import signal

# ── Config ──────────────────────────────────────────────────────────────────
ALIVE_CHAR = "█"
DEAD_CHAR  = " "
FPS        = 12
DENSITY    = 0.35

# ANSI palette for living cells (cycles by age)
PALETTE = [
    "\033[38;5;82m",   # bright green
    "\033[38;5;46m",   # lime
    "\033[38;5;148m",  # chartreuse
    "\033[38;5;220m",  # gold
    "\033[38;5;214m",  # orange
    "\033[38;5;202m",  # red-orange
]
RESET = "\033[0m"

# ── Grid helpers ────────────────────────────────────────────────────────────

def make_grid(rows, cols, density=DENSITY):
    return [[random.random() < density for _ in range(cols)] for _ in range(rows)]


def step(grid, rows, cols):
    new = [[False] * cols for _ in range(rows)]
    for r in range(rows):
        for c in range(cols):
            n = 0
            for dr in (-1, 0, 1):
                for dc in (-1, 0, 1):
                    if dr == 0 and dc == 0:
                        continue
                    n += grid[(r + dr) % rows][(c + dc) % cols]
            if grid[r][c]:
                new[r][c] = n in (2, 3)
            else:
                new[r][c] = n == 3
    return new


def update_ages(old_grid, new_grid, old_ages, rows, cols):
    ages = [[0] * cols for _ in range(rows)]
    for r in range(rows):
        for c in range(cols):
            if new_grid[r][c]:
                ages[r][c] = (old_ages[r][c] + 1) if old_grid[r][c] else 1
    return ages


def render(grid, ages, rows, cols):
    lines = []
    for r in range(rows):
        line = []
        for c in range(cols):
            if grid[r][c]:
                color = PALETTE[min(ages[r][c] - 1, len(PALETTE) - 1)]
                line.append(f"{color}{ALIVE_CHAR}{RESET}")
            else:
                line.append(DEAD_CHAR)
        lines.append("".join(line))
    return "\n".join(lines)


def population(grid):
    return sum(sum(row) for row in grid)


# ── Main loop ───────────────────────────────────────────────────────────────

def main():
    signal.signal(signal.SIGINT, lambda *_: (print(RESET), sys.exit(0)))

    try:
        cols, rows = os.get_terminal_size().columns, os.get_terminal_size().lines - 3
    except OSError:
        cols, rows = 80, 22

    grid = make_grid(rows, cols)
    ages = [[1 if grid[r][c] else 0 for c in range(cols)] for r in range(rows)]
    gen = 0

    sys.stdout.write("\033[?25l")  # hide cursor
    sys.stdout.flush()

    try:
        while True:
            frame = render(grid, ages, rows, cols)
            pop = population(grid)
            stats = f" gen {gen:>5}  │  pop {pop:>5}/{rows * cols} "
            bar = "─" * len(stats)
            sys.stdout.write(f"\033[H{bar}\n{stats}\n{bar}\n{frame}")
            sys.stdout.flush()

            old_grid = grid
            new_grid = step(old_grid, rows, cols)
            ages = update_ages(old_grid, new_grid, ages, rows, cols)
            grid = new_grid
            gen += 1
            time.sleep(1 / FPS)
    finally:
        sys.stdout.write(f"{RESET}\033[?25h")  # restore cursor
        sys.stdout.flush()


if __name__ == "__main__":
    main()
