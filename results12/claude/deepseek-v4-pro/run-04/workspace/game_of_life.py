#!/usr/bin/env python3
"""Conway's Game of Life — interactive terminal edition.

Controls:
  Arrows / hjkl  — Move cursor
  Space / Enter  — Toggle cell
  p              — Play/pause simulation
  s              — Step one generation (when paused)
  c              — Clear the grid
  r              — Randomize the grid
  1-5            — Load preset patterns
  +/-            — Adjust speed
  q              — Quit
"""

import curses
import random
import time
from typing import Set, Tuple

Cell = Tuple[int, int]
Grid = Set[Cell]

# ── Preset patterns ──────────────────────────────────────────────────────────

PRESETS = {
    "1": {  # Glider
        "name": "Glider",
        "cells": [(0, 1), (1, 2), (2, 0), (2, 1), (2, 2)],
    },
    "2": {  # Lightweight spaceship
        "name": "LWSS",
        "cells": [
            (0, 1), (0, 4),
            (1, 0),
            (2, 0), (2, 4),
            (3, 0), (3, 1), (3, 2), (3, 3),
        ],
    },
    "3": {  # Pulsar
        "name": "Pulsar",
        "cells": [
            (2, 4), (2, 5), (2, 6), (2, 10), (2, 11), (2, 12),
            (4, 2), (5, 2), (6, 2), (4, 7), (5, 7), (6, 7),
            (4, 9), (5, 9), (6, 9), (4, 14), (5, 14), (6, 14),
            (7, 4), (7, 5), (7, 6), (7, 10), (7, 11), (7, 12),
            (9, 4), (9, 5), (9, 6), (9, 10), (9, 11), (9, 12),
            (10, 2), (11, 2), (12, 2), (10, 7), (11, 7), (12, 7),
            (10, 9), (11, 9), (12, 9), (10, 14), (11, 14), (12, 14),
            (14, 4), (14, 5), (14, 6), (14, 10), (14, 11), (14, 12),
        ],
    },
    "4": {  # Gosper glider gun
        "name": "Gosper Gun",
        "cells": [
            (5, 1), (5, 2), (6, 1), (6, 2),
            (5, 11), (6, 11), (7, 11), (4, 12), (8, 12), (3, 13), (9, 13),
            (3, 14), (9, 14), (6, 15), (4, 16), (8, 16), (5, 17), (6, 17),
            (7, 17), (6, 18), (3, 21), (4, 21), (5, 21), (3, 22), (4, 22),
            (5, 22), (2, 23), (6, 23), (1, 25), (2, 25), (6, 25), (7, 25),
            (3, 35), (4, 35), (3, 36), (4, 36),
        ],
    },
    "5": {  # R-pentomino
        "name": "R-Pentomino",
        "cells": [(0, 1), (0, 2), (1, 0), (1, 1), (2, 1)],
    },
}

# ── Game logic ────────────────────────────────────────────────────────────────

NEIGHBORS = [(-1, -1), (-1, 0), (-1, 1), (0, -1), (0, 1), (1, -1), (1, 0), (1, 1)]


def step(grid: Grid) -> Grid:
    """Compute the next generation."""
    candidates = {coord for cell in grid for coord in neighbors_of(cell)}
    candidates.update(grid)

    next_grid: Grid = set()
    for (r, c) in candidates:
        n = sum(1 for dr, dc in NEIGHBORS if (r + dr, c + dc) in grid)
        if n == 3 or (n == 2 and (r, c) in grid):
            next_grid.add((r, c))
    return next_grid


def neighbors_of(cell: Cell) -> Set[Cell]:
    r, c = cell
    return {(r + dr, c + dc) for dr, dc in NEIGHBORS}


def place_pattern(grid: Grid, cells: list, offset_r: int, offset_c: int) -> Grid:
    return grid | {(r + offset_r, c + offset_c) for (r, c) in cells}


def randomize(grid: Grid, rows: int, cols: int, density: float = 0.3) -> Grid:
    return {(r, c) for r in range(rows) for c in range(cols) if random.random() < density}


# ── Rendering ─────────────────────────────────────────────────────────────────

def draw_grid(stdscr, grid: Grid, cursor: Cell, rows: int, cols: int,
              playing: bool, speed: float, gen: int, pop: int, msg: str):
    stdscr.erase()

    for r in range(rows):
        for c in range(cols):
            y, x = r + 1, c * 2 + 1
            if (r, c) in grid:
                stdscr.addch(y, x, "█", curses.A_REVERSE)
                stdscr.addch(y, x + 1, "█", curses.A_REVERSE)
            else:
                stdscr.addch(y, x, "·")
                stdscr.addch(y, x + 1, "·")

    # Cursor
    cy, cx = cursor[0] + 1, cursor[1] * 2 + 1
    stdscr.addch(cy, cx, "[", curses.A_BOLD)
    stdscr.addch(cy, cx + 2, "]", curses.A_BOLD)

    # Status bar
    status = (
        f" Gen: {gen:<6} Pop: {pop:<6} Speed: {speed:.1f}x "
        f"{'▶ PLAYING' if playing else '⏸ PAUSED'} "
        f"| {msg} "
    )
    try:
        stdscr.addstr(rows + 1, 1, status[:cols * 2 - 1], curses.A_REVERSE)
    except curses.error:
        pass

    # Help bar
    help_text = (
        " arrows/hjkl:move  space:toggle  p:play  s:step  c:clear  r:random  "
        "1-5:presets  +/-:speed  q:quit"
    )
    try:
        stdscr.addstr(rows + 2, 1, help_text[:cols * 2 - 1], curses.A_DIM)
    except curses.error:
        pass

    stdscr.refresh()


# ── Main loop ─────────────────────────────────────────────────────────────────

def main(stdscr):
    curses.curs_set(0)
    stdscr.nodelay(True)
    stdscr.timeout(50)

    # Determine grid size from terminal
    max_y, max_x = stdscr.getmaxyx()
    rows = min(max_y - 4, 60)
    cols = min((max_x - 1) // 2, 80)

    grid: Grid = set()
    cursor = (rows // 2, cols // 2)
    playing = False
    speed = 5.0       # generations per tick
    gen = 0
    msg = "Welcome! Press 'r' to randomize or '1'-'5' for presets."
    tick_accum = 0.0

    # Key-to-delta mapping
    keymap = {
        curses.KEY_UP:    (-1, 0),
        curses.KEY_DOWN:  (1, 0),
        curses.KEY_LEFT:  (0, -1),
        curses.KEY_RIGHT: (0, 1),
        ord("k"): (-1, 0),
        ord("j"): (1, 0),
        ord("h"): (0, -1),
        ord("l"): (0, 1),
    }

    while True:
        # Input
        key = stdscr.getch()
        msg = ""

        if key == ord("q"):
            break
        elif key == ord("p"):
            playing = not playing
            msg = "▶ Playing" if playing else "⏸ Paused"
        elif key == ord("s") and not playing:
            grid = step(grid)
            gen += 1
            msg = "Stepped →"
        elif key == ord("c"):
            grid.clear()
            gen = 0
            playing = False
            msg = "Cleared"
        elif key == ord("r"):
            grid = randomize(grid, rows, cols, 0.3)
            gen = 0
            msg = "Randomized"
        elif key in (ord("+"), ord("=")):
            speed = min(speed + 1, 30)
            msg = f"Speed: {speed:.0f}x"
        elif key == ord("-"):
            speed = max(speed - 1, 1)
            msg = f"Speed: {speed:.0f}x"
        elif chr(key) in PRESETS:
            preset = PRESETS[chr(key)]
            grid = place_pattern(set(), preset["cells"], rows // 2, cols // 2)
            gen = 0
            playing = False
            msg = f"Loaded: {preset['name']}"
        elif key == ord(" ") or key == ord("\n"):
            cell = (cursor[0], cursor[1])
            if cell in grid:
                grid.discard(cell)
            else:
                grid.add(cell)
            msg = "Toggled"
        elif key in keymap:
            dr, dc = keymap[key]
            cursor = (
                max(0, min(rows - 1, cursor[0] + dr)),
                max(0, min(cols - 1, cursor[1] + dc)),
            )
        elif key == curses.KEY_RESIZE:
            max_y, max_x = stdscr.getmaxyx()
            rows = min(max_y - 4, 60)
            cols = min((max_x - 1) // 2, 80)
            cursor = (min(cursor[0], rows - 1), min(cursor[1], cols - 1))

        # Simulation tick
        if playing:
            tick_accum += speed * 0.05  # 50ms tick → ~20 fps base
            while tick_accum >= 1.0:
                grid = step(grid)
                gen += 1
                tick_accum -= 1.0
            if not grid:
                playing = False
                msg = "Extinct! Simulation stopped."

        # Render
        draw_grid(stdscr, grid, cursor, rows, cols, playing, speed, gen, len(grid), msg)

        # Idle message fade
        if not msg and not playing:
            msg = ""


if __name__ == "__main__":
    curses.wrapper(main)