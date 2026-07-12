#!/usr/bin/env python3
"""
Conway's Game of Life — terminal edition 🧬
Run:  python3 life.py
Stop: Ctrl-C
"""

import os, sys, time, random

# ── configuration ──────────────────────────────────────────────
ALIVE = "█"
DEAD  = " "
FPS   = 12
SEED_DENSITY = 0.3

# ANSI color palette (foreground)
COLORS = [
    "\033[38;5;196m",  # red
    "\033[38;5;208m",  # orange
    "\033[38;5;226m",  # yellow
    "\033[38;5;46m",   # green
    "\033[38;5;51m",   # cyan
    "\033[38;5;21m",   # blue
    "\033[38;5;201m",  # magenta
]
RESET = "\033[0m"

# ── helpers ────────────────────────────────────────────────────

def terminal_size():
    cols, rows = os.get_terminal_size()
    return rows - 1, cols  # leave one row for the status line

def make_grid(rows, cols):
    return [[random.random() < SEED_DENSITY for c in range(cols)] for r in range(rows)]

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
    births = 0
    deaths = 0
    for r in range(rows):
        for c in range(cols):
            n = neighbours(grid, r, c, rows, cols)
            if grid[r][c]:
                alive = n in (2, 3)
                if not alive:
                    deaths += 1
            else:
                alive = n == 3
                if alive:
                    births += 1
            new[r][c] = alive
    return new, births, deaths

def render(grid, rows, cols, generation, population, births, deaths):
    color = COLORS[generation % len(COLORS)]
    buf = ["\033[H"]  # cursor home
    for r in range(rows):
        row_chars = []
        for c in range(cols):
            row_chars.append(f"{color}{ALIVE}{RESET}" if grid[r][c] else DEAD)
        buf.append("".join(row_chars))
    status = (
        f" Gen {generation:>6}  |  "
        f"Pop {population:>6}  |  "
        f"Born {births:>5}  |  "
        f"Died {deaths:>5}  "
    )
    buf.append(f"\033[7m{status:<{cols}}\033[0m")
    sys.stdout.write("\n".join(buf))
    sys.stdout.flush()

# ── main loop ──────────────────────────────────────────────────

def main():
    rows, cols = terminal_size()
    grid = make_grid(rows, cols)
    generation = 0

    sys.stdout.write("\033[2J")  # clear screen
    sys.stdout.write("\033[?25l")  # hide cursor

    try:
        while True:
            population = sum(cell for row in grid for cell in row)
            grid, births, deaths = step(grid, rows, cols)
            generation += 1
            render(grid, rows, cols, generation, population, births, deaths)
            time.sleep(1 / FPS)
    except KeyboardInterrupt:
        pass
    finally:
        sys.stdout.write("\033[?25h\n")  # show cursor

if __name__ == "__main__":
    main()
