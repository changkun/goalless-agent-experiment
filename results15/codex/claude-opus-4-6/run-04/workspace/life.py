#!/usr/bin/env python3
"""
Conway's Game of Life — terminal edition.

Run:  python3 life.py
Keys: q to quit, r to randomize, SPACE to pause/resume.
"""

import curses
import random
import time


def make_grid(rows, cols, density=0.3):
    return [[random.random() < density for _ in range(cols)] for _ in range(rows)]


def neighbors(grid, r, c, rows, cols):
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
            n = neighbors(grid, r, c, rows, cols)
            if grid[r][c]:
                new[r][c] = n in (2, 3)
            else:
                new[r][c] = n == 3
    return new


BLOCKS = {
    (True, True):   "█",
    (True, False):  "▀",
    (False, True):  "▄",
    (False, False): " ",
}


def draw(stdscr, grid, rows, cols, generation, paused):
    stdscr.erase()
    max_y, max_x = stdscr.getmaxyx()

    display_rows = min(rows // 2, max_y - 1)
    display_cols = min(cols, max_x)

    has_colors = curses.has_colors()
    if has_colors:
        attr = curses.color_pair(1)
    else:
        attr = 0

    for yr in range(display_rows):
        r_top = yr * 2
        r_bot = r_top + 1
        line_parts = []
        for c in range(display_cols):
            top = grid[r_top][c] if r_top < rows else False
            bot = grid[r_bot][c] if r_bot < rows else False
            line_parts.append(BLOCKS[(top, bot)])
        line = "".join(line_parts)
        try:
            stdscr.addstr(yr, 0, line, attr)
        except curses.error:
            pass

    status = f" Gen {generation}  |  {'PAUSED' if paused else 'Running'}  |  [q]uit [r]andomize [space]pause "
    try:
        stdscr.addstr(max_y - 1, 0, status[:max_x - 1], curses.A_REVERSE)
    except curses.error:
        pass

    stdscr.refresh()


def main(stdscr):
    curses.curs_set(0)
    stdscr.nodelay(True)
    stdscr.timeout(80)

    if curses.has_colors():
        curses.start_color()
        curses.use_default_colors()
        curses.init_pair(1, curses.COLOR_GREEN, -1)

    max_y, max_x = stdscr.getmaxyx()
    rows = (max_y - 1) * 2
    cols = max_x

    grid = make_grid(rows, cols)
    generation = 0
    paused = False

    while True:
        draw(stdscr, grid, rows, cols, generation, paused)

        key = stdscr.getch()
        if key == ord("q"):
            break
        elif key == ord("r"):
            grid = make_grid(rows, cols)
            generation = 0
        elif key == ord(" "):
            paused = not paused

        if not paused:
            grid = step(grid, rows, cols)
            generation += 1


if __name__ == "__main__":
    curses.wrapper(main)
