#!/usr/bin/env python3
"""A tiny terminal Conway's Game of Life.

Usage:
    ./life.py [options]

Examples:
    ./life.py                     # glider gun pattern
    ./life.py --pattern pento     # r-pentomino
    ./life.py --fps 20 --size 40x20
"""

import argparse
import random
import shutil
import sys
import time

# Character set: live cells are bright, dead cells are dim dots.
LIVE = "\033[1;32m#\033[0m"
DEAD = "\033[2;37m.\033[0m"


def parse_size(text):
    try:
        w, h = text.lower().split("x")
        return int(w), int(h)
    except ValueError:
        raise argparse.ArgumentTypeError("size must be like 40x20")


def empty(w, h):
    return [[0] * w for _ in range(h)]


def set_cells(grid, *coords):
    for x, y in coords:
        if 0 <= y < len(grid) and 0 <= x < len(grid[0]):
            grid[y][x] = 1


def pattern(name, w, h):
    """Return a grid with the requested starting pattern, centered."""
    g = empty(w, h)
    if name == "glider":
        ox, oy = w // 2 - 1, h // 2 - 1
        set_cells(g, (ox + 1, oy), (ox + 2, oy + 1), (ox, oy + 2),
                  (ox + 1, oy + 2), (ox + 2, oy + 2))
    elif name == "gz":  # Gosper glider gun
        ox, oy = w // 2 - 18, h // 2 - 5
        set_cells(
            g,
            (ox + 1, oy + 5), (ox + 1, oy + 6), (ox + 2, oy + 5), (ox + 2, oy + 6),
            (ox + 11, oy + 5), (ox + 11, oy + 6), (ox + 11, oy + 7),
            (ox + 12, oy + 4), (ox + 12, oy + 8), (ox + 13, oy + 3),
            (ox + 14, oy + 3), (ox + 15, oy + 6), (ox + 16, oy + 4),
            (ox + 16, oy + 8), (ox + 17, oy + 5), (ox + 17, oy + 6),
            (ox + 17, oy + 7), (ox + 18, oy + 6), (ox + 21, oy + 3),
            (ox + 21, oy + 4), (ox + 21, oy + 5), (ox + 22, oy + 3),
            (ox + 22, oy + 4), (ox + 22, oy + 5), (ox + 23, oy + 2),
            (ox + 23, oy + 6), (ox + 25, oy + 1), (ox + 25, oy + 2),
            (ox + 25, oy + 6), (ox + 25, oy + 7), (ox + 35, oy + 3),
            (ox + 36, oy + 3), (ox + 35, oy + 4), (ox + 36, oy + 4),
        )
    elif name == "pento":  # R-pentomino
        cx, cy = w // 2, h // 2
        set_cells(g, (cx, cy), (cx + 1, cy), (cx - 1, cy + 1),
                  (cx, cy + 1), (cx + 1, cy + 2))
    elif name == "random":
        for y in range(h):
            for x in range(w):
                g[y][x] = 1 if random.random() < 0.35 else 0
    else:
        raise ValueError("unknown pattern: %s" % name)
    return g


def neighbors(grid, x, y, w, h):
    n = 0
    for dy in (-1, 0, 1):
        for dx in (-1, 0, 1):
            if dx == 0 and dy == 0:
                continue
            if 0 <= y + dy < h and 0 <= x + dx < w:
                n += grid[y + dy][x + dx]
    return n


def step(grid, w, h):
    nxt = empty(w, h)
    for y in range(h):
        for x in range(w):
            n = neighbors(grid, x, y, w, h)
            if grid[y][x]:
                nxt[y][x] = 1 if n in (2, 3) else 0
            else:
                nxt[y][x] = 1 if n == 3 else 0
    return nxt


def render(grid):
    return "\n".join("".join(LIVE if c else DEAD for c in row) for row in grid)


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--pattern", default="gz",
                    choices=["glider", "gz", "pento", "random"])
    ap.add_argument("--size", default=None, type=parse_size,
                    help="grid size as WxH, e.g. 40x20 (defaults to terminal size)")
    ap.add_argument("--fps", default=10, type=int, help="frames per second")
    ap.add_argument("--gen", default=None, type=int,
                    help="run for exactly N generations then exit")
    args = ap.parse_args()

    if args.size:
        w, h = args.size
    else:
        cols, rows = shutil.get_terminal_size((80, 24))
        w, h = cols - 1, rows - 2

    grid = pattern(args.pattern, w, h)
    period = 1.0 / max(1, args.fps)
    gen = 0

    try:
        while True:
            sys.stdout.write("\033[H" + render(grid))
            sys.stdout.flush()
            if args.gen is not None and gen >= args.gen:
                break
            grid = step(grid, w, h)
            gen += 1
            time.sleep(period)
    except KeyboardInterrupt:
        print("\nStopped after %d generations." % gen)


if __name__ == "__main__":
    main()
