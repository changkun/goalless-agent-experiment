#!/usr/bin/env python3
"""Conway's Game of Life - tiny terminal simulator.

Controls (while running):
  space  pause / resume
  n      step once (when paused)
  r      reset to current pattern
  1-5    load built-in pattern
  q      quit
"""

import curses
import os
import sys
import time
from typing import Dict, Set, Tuple

Cell = Tuple[int, int]


def glider() -> Set[Cell]:
    return {(0, 1), (1, 2), (2, 0), (2, 1), (2, 2)}


def blinker() -> Set[Cell]:
    return {(0, 0), (0, 1), (0, 2)}


def pulsar() -> Set[Cell]:
    coords = [
        (-6, -4), (-6, -3), (-6, -2), (-1, -4), (-1, -3), (-1, -2),
        (-4, -6), (-3, -6), (-2, -6), (-4, -1), (-3, -1), (-2, -1),
        (2, -6), (3, -6), (4, -6), (2, -1), (3, -1), (4, -1),
        (6, -4), (6, -3), (6, -2), (1, -4), (1, -3), (1, -2),
        (-6, 2), (-6, 3), (-6, 4), (-1, 2), (-1, 3), (-1, 4),
        (6, 2), (6, 3), (6, 4), (1, 2), (1, 3), (1, 4),
        (-4, 6), (-3, 6), (-2, 6), (-4, 1), (-3, 1), (-2, 1),
        (2, 6), (3, 6), (4, 6), (2, 1), (3, 1), (4, 1),
    ]
    return set(coords)


def gosper_gun() -> Set[Cell]:
    base = [
        (0, 4), (0, 5), (1, 4), (1, 5),
        (10, 4), (10, 5), (10, 6), (11, 3), (11, 7), (12, 2), (12, 8),
        (13, 2), (13, 8), (14, 5), (15, 3), (15, 7), (16, 4), (16, 5),
        (16, 6), (17, 5),
        (20, 2), (20, 3), (20, 4), (21, 2), (21, 3), (21, 4),
        (22, 1), (22, 5), (24, 0), (24, 1), (24, 5), (24, 6),
        (34, 2), (34, 3), (35, 2), (35, 3),
    ]
    return {(r - 5, c - 18) for r, c in base}


def acorn() -> Set[Cell]:
    return {(0, 1), (1, 3), (2, 0), (2, 1), (2, 4), (2, 5), (2, 6)}


PATTERNS = {
    "1": ("Glider", glider),
    "2": ("Blinker", blinker),
    "3": ("Pulsar", pulsar),
    "4": ("Gosper Gun", gosper_gun),
    "5": ("Acorn", acorn),
}


def step(cells: Set[Cell]) -> Set[Cell]:
    neighbor_counts: Dict[Cell, int] = {}
    for r, c in cells:
        for dr in (-1, 0, 1):
            for dc in (-1, 0, 1):
                if dr == 0 and dc == 0:
                    continue
                nb = (r + dr, c + dc)
                neighbor_counts[nb] = neighbor_counts.get(nb, 0) + 1

    new: Set[Cell] = set()
    for cell, n in neighbor_counts.items():
        if n == 3 or (n == 2 and cell in cells):
            new.add(cell)
    return new


def bounds(cells: Set[Cell], height: int, width: int) -> Tuple[int, int, int, int]:
    if not cells:
        return 0, height, 0, width
    rs = [r for r, _ in cells]
    cs = [c for _, c in cells]
    r0, r1 = min(rs) - 2, max(rs) + 3
    c0, c1 = min(cs) - 2, max(cs) + 3
    r0 = max(r0, 0)
    c0 = max(c0, 0)
    r1 = min(r1, height)
    c1 = min(c1, width)
    return r0, r1, c0, c1


def run(stdscr) -> None:
    curses.curs_set(0)
    stdscr.nodelay(True)
    stdscr.timeout(120)

    height, width = stdscr.getmaxyx()
    grid_h = max(1, height - 1)
    grid_w = width

    name, builder = PATTERNS["1"]
    cells: Set[Cell] = builder()
    initial: Set[Cell] = set(cells)
    paused = False
    gen = 0
    fps = 12.0
    last = time.time()

    while True:
        ch = stdscr.getch()
        if ch in (ord("q"), 27):
            return
        elif ch == ord(" "):
            paused = not paused
        elif ch == ord("n"):
            cells = step(cells)
            gen += 1
        elif ch == ord("r"):
            cells = set(initial)
            gen = 0
        elif ch in (ord("1"), ord("2"), ord("3"), ord("4"), ord("5")):
            name, builder = PATTERNS[chr(ch)]
            initial = builder()
            cells = set(initial)
            gen = 0

        now = time.time()
        if not paused and now - last >= 1.0 / fps:
            cells = step(cells)
            gen += 1
            last = now

        stdscr.erase()
        r0, r1, c0, c1 = bounds(cells, grid_h, grid_w)
        for r in range(r0, r1):
            try:
                line = "".join("#" if (r, c) in cells else " " for c in range(c0, c1))
                stdscr.addnstr(r, 0, line, c1 - c0, curses.color_pair(1))
            except curses.error:
                pass

        status = f" {name}  gen={gen}  pop={len(cells)}  {'PAUSED' if paused else 'play'}  [space]n r 1-5 q "
        try:
            stdscr.addnstr(0, 0, status.ljust(max(0, width - 1)), max(0, width - 1),
                           curses.A_REVERSE | curses.color_pair(2))
        except curses.error:
            pass

        stdscr.refresh()


def main() -> int:
    if not sys.stdout.isatty() or os.environ.get("LIFE_DEMO") == "1":
        demo()
        return 0

    curses.start_color()
    curses.use_default_colors()
    curses.init_pair(1, curses.COLOR_GREEN, -1)
    curses.init_pair(2, curses.COLOR_BLACK, curses.COLOR_CYAN)
    try:
        curses.wrapper(run)
    except KeyboardInterrupt:
        pass
    return 0


def demo() -> None:
    """Plain-text preview of the glider running 30 generations."""
    cells = glider()
    for gen in range(30):
        grid = [[" "] * 20 for _ in range(10)]
        for r, c in cells:
            if 0 <= r < 10 and 0 <= c < 20:
                grid[r][c] = "#"
        print(f"gen {gen:02d}: " + "".join("".join(row) for row in grid))
        cells = step(cells)


if __name__ == "__main__":
    sys.exit(main())
