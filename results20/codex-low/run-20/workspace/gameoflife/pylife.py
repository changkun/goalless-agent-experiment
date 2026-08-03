#!/usr/bin/env python3
"""pylife - Conway's Game of Life rendered in the terminal.

Pure standard library, cross-platform friendly. Press Ctrl-C to stop.
"""
import argparse
import os
import random
import shutil
import sys
import time

ALIVE = "#"
DEAD = " "


def clear():
    # Windows vs POSIX
    os.system("cls" if os.name == "nt" else "clear")


def make_grid(h, w):
    return [[DEAD for _ in range(w)] for _ in range(h)]


def count_neighbors(g, x, y):
    h, w = len(g), len(g[0])
    total = 0
    for dy in (-1, 0, 1):
        for dx in (-1, 0, 1):
            if dx == 0 and dy == 0:
                continue
            total += g[(y + dy) % h][(x + dx) % w] == ALIVE
    return total


def next_generation(g):
    h, w = len(g), len(g[0])
    ng = make_grid(h, w)
    for y in range(h):
        for x in range(w):
            n = count_neighbors(g, x, y)
            if g[y][x] == ALIVE:
                ng[y][x] = ALIVE if n in (2, 3) else DEAD
            else:
                ng[y][x] = ALIVE if n == 3 else DEAD
    return ng


def render(g):
    return "\n".join("".join(row) for row in g)


def random_seed(g, density):
    for y in range(len(g)):
        for x in range(len(g[0])):
            if random.random() < density:
                g[y][x] = ALIVE


def stamp(g, x, y, pattern):
    for py, row in enumerate(pattern):
        for px, ch in enumerate(row):
            if ch == ALIVE:
                g[y + py][x + px] = ALIVE


GLIDER = [
    ".#.",
    "..#",
    "###",
]

LWSS = [  # lightweight spaceship
    ".#..#",
    "#....",
    "#...#",
    "####.",
]

GOSPER = [  # Gosper glider gun
    "........................#...........",
    "......................#.#...........",
    "............##......##............##",
    "...........#...#....##............##",
    "##........#.....#...##..............",
    "##........#...#.##....#.#...........",
    "..........#.....#.......#...........",
    "...........#...#....................",
    "............##......................",
]

PULSAR = [
    "..###....###..",
    ".............",
    "#....#..#....#",
    "#....#..#....#",
    "#....#..#....#",
    "..###....###..",
    ".............",
    "..###....###..",
    "#....#..#....#",
    "#....#..#....#",
    "#....#..#....#",
    ".............",
    "..###....###..",
]

PATTERNS = {
    "random": None,
    "glider": GLIDER,
    "lwss": LWSS,
    "gosper": GOSPER,
    "pulsar": PULSAR,
}


def main():
    parser = argparse.ArgumentParser(description="Conway's Game of Life in your terminal")
    parser.add_argument("--pattern", choices=PATTERNS, default="random",
                        help="starting pattern")
    parser.add_argument("--density", type=float, default=0.3,
                        help="fill density for 'random' (0.0-1.0)")
    parser.add_argument("--fps", type=float, default=12.0,
                        help="animation speed in frames per second")
    parser.add_argument("--frames", type=int, default=0,
                        help="stop after N frames (0 = run forever)")
    parser.add_argument("--cols", type=int, default=0,
                        help="grid columns (0 = auto from terminal)")
    parser.add_argument("--rows", type=int, default=0,
                        help="grid rows (0 = auto from terminal)")
    args = parser.parse_args()

    cols = args.cols or shutil.get_terminal_size((80, 24)).columns
    rows = args.rows or shutil.get_terminal_size((80, 24)).lines - 2

    g = make_grid(rows, cols)

    pattern = PATTERNS[args.pattern]
    if pattern is None:
        random_seed(g, max(0.0, min(1.0, args.density)))
        stamp(g, cols // 2, rows // 2, GLIDER)
    else:
        stamp(g, cols // 2 - len(pattern[0]) // 2,
                 rows // 2 - len(pattern) // 2, pattern)

    delay = 1.0 / max(0.1, args.fps)
    frame = 0
    try:
        while args.frames == 0 or frame < args.frames:
            clear()
            sys.stdout.write("\x1b[?25l")          # hide cursor
            sys.stdout.write(render(g))
            sys.stdout.flush()
            g = next_generation(g)
            frame += 1
            time.sleep(delay)
    except KeyboardInterrupt:
        pass
    finally:
        sys.stdout.write("\x1b[?25h")              # restore cursor
        sys.stdout.write("\n")


if __name__ == "__main__":
    main()
