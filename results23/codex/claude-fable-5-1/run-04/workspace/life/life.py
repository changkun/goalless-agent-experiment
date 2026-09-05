#!/usr/bin/env python3
"""A tiny terminal Conway's Game of Life.

Usage:
    python3 life.py [--pattern NAME] [--width N] [--height N]
                    [--gens N] [--delay SECONDS] [--seed N]

Patterns: random (default), glider, gosper, pulsar, rpentomino
"""

from __future__ import annotations

import argparse
import random
import sys
import time

ALIVE = "█"
DEAD = " "

PATTERNS: dict[str, list[str]] = {
    "glider": [
        ".#.",
        "..#",
        "###",
    ],
    "rpentomino": [
        ".##",
        "##.",
        ".#.",
    ],
    "pulsar": [
        "..###...###..",
        ".............",
        "#....#.#....#",
        "#....#.#....#",
        "#....#.#....#",
        "..###...###..",
        ".............",
        "..###...###..",
        "#....#.#....#",
        "#....#.#....#",
        "#....#.#....#",
        ".............",
        "..###...###..",
    ],
    "gosper": [
        "........................#...........",
        "......................#.#...........",
        "............##......##............##",
        "...........#...#....##............##",
        "##........#.....#...##..............",
        "##........#...#.##....#.#...........",
        "..........#.....#.......#...........",
        "...........#...#....................",
        "............##......................",
    ],
}

Cells = set[tuple[int, int]]


def parse_pattern(rows: list[str], width: int, height: int) -> Cells:
    """Center a pattern of '#'/'.' rows on a width x height grid."""
    pattern_height = len(rows)
    pattern_width = max(len(row) for row in rows)
    top = max(0, (height - pattern_height) // 2)
    left = max(0, (width - pattern_width) // 2)
    return {
        (left + col, top + row_index)
        for row_index, row in enumerate(rows)
        for col, char in enumerate(row)
        if char == "#"
    }


def random_cells(width: int, height: int, density: float, rng: random.Random) -> Cells:
    return {
        (x, y)
        for y in range(height)
        for x in range(width)
        if rng.random() < density
    }


def step(cells: Cells, width: int, height: int) -> Cells:
    """Advance one generation on a toroidal (wrapping) grid."""
    neighbor_counts: dict[tuple[int, int], int] = {}
    for x, y in cells:
        for dx in (-1, 0, 1):
            for dy in (-1, 0, 1):
                if dx == 0 and dy == 0:
                    continue
                key = ((x + dx) % width, (y + dy) % height)
                neighbor_counts[key] = neighbor_counts.get(key, 0) + 1
    return {
        cell
        for cell, count in neighbor_counts.items()
        if count == 3 or (count == 2 and cell in cells)
    }


def render(cells: Cells, width: int, height: int, generation: int) -> str:
    lines = [
        "".join(ALIVE if (x, y) in cells else DEAD for x in range(width))
        for y in range(height)
    ]
    header = f" gen {generation:>5}  alive {len(cells):>5}  (Ctrl-C to quit)"
    return "\n".join([header, "+" + "-" * width + "+"] + [f"|{line}|" for line in lines] + ["+" + "-" * width + "+"])


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Terminal Conway's Game of Life")
    parser.add_argument("--pattern", default="random", choices=["random", *PATTERNS])
    parser.add_argument("--width", type=int, default=60)
    parser.add_argument("--height", type=int, default=24)
    parser.add_argument("--gens", type=int, default=0, help="stop after N generations (0 = run forever)")
    parser.add_argument("--delay", type=float, default=0.08, help="seconds between frames")
    parser.add_argument("--density", type=float, default=0.3, help="fill ratio for random pattern")
    parser.add_argument("--seed", type=int, default=None)
    args = parser.parse_args(argv)

    if args.pattern == "random":
        cells = random_cells(args.width, args.height, args.density, random.Random(args.seed))
    else:
        cells = parse_pattern(PATTERNS[args.pattern], args.width, args.height)

    generation = 0
    clear = "\033[H\033[J"
    try:
        while True:
            sys.stdout.write(clear + render(cells, args.width, args.height, generation) + "\n")
            sys.stdout.flush()
            if args.gens and generation >= args.gens:
                break
            if not cells:
                print("Everything died. The end.")
                break
            time.sleep(args.delay)
            cells = step(cells, args.width, args.height)
            generation += 1
    except KeyboardInterrupt:
        print()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
