#!/usr/bin/env python3
"""Conway's Game of Life — terminal edition.

A self-contained simulator with a small library of classic patterns.
Run with `python3 life.py` and press Ctrl-C to exit.
"""
from __future__ import annotations

import os
import shutil
import sys
import time
from collections.abc import Iterable

# A live cell is a (row, col) tuple. The universe is the set of live cells.
Cell = tuple[int, int]


# --------------------------------------------------------------------------- #
# Pattern library. Each pattern is given as a list of strings; '#' means alive.
# --------------------------------------------------------------------------- #
PATTERNS: dict[str, list[str]] = {
    "glider": [
        ".#.",
        "..#",
        "###",
    ],
    "blinker": ["###"],
    "toad": [
        ".###",
        "###.",
    ],
    "beacon": [
        "##..",
        "##..",
        "..##",
        "..##",
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
    "gosper-glider-gun": [
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
    "lwss": [  # light-weight spaceship
        ".#..#",
        "#....",
        "#...#",
        "####.",
    ],
}


def parse(rows: Iterable[str]) -> set[Cell]:
    """Turn ASCII rows into a set of live cells."""
    return {
        (r, c)
        for r, line in enumerate(rows)
        for c, ch in enumerate(line)
        if ch == "#"
    }


# --------------------------------------------------------------------------- #
# The rules
# --------------------------------------------------------------------------- #
NEIGHBORS = [(-1, -1), (-1, 0), (-1, 1), (0, -1), (0, 1), (1, -1), (1, 0), (1, 1)]


def step(live: set[Cell]) -> set[Cell]:
    """Advance one generation under Conway's rules.

    Only cells currently alive, or neighbours of an alive cell, can possibly
    become/stay alive — so we iterate over that frontier, not the whole plane.
    """
    counts: dict[Cell, int] = {}
    for r, c in live:
        for dr, dc in NEIGHBORS:
            counts[(r + dr, c + dc)] = counts.get((r + dr, c + dc), 0) + 1

    nxt: set[Cell] = set()
    for cell, n in counts.items():
        if n == 3 or (n == 2 and cell in live):
            nxt.add(cell)
    return nxt


# --------------------------------------------------------------------------- #
# Rendering
# --------------------------------------------------------------------------- #
LIVE = "█"
DEAD = "·"


def render(live: set[Cell], gen: int, cols: int, rows: int) -> str:
    """Build a single frame sized to the terminal."""
    out = [f"  gen {gen:<6} population {len(live):<6}\n"]
    for r in range(rows):
        line = []
        for c in range(cols):
            line.append(LIVE if (r, c) in live else DEAD)
        out.append("".join(line))
        out.append("\n")
    return "".join(out)


def clear() -> None:
    sys.stdout.write("\033[H\033[J")
    sys.stdout.flush()


# --------------------------------------------------------------------------- #
# Main
# --------------------------------------------------------------------------- #
def main() -> None:
    cols, rows = shutil.get_terminal_size((80, 24))
    rows = max(rows - 3, 8)  # leave room for the header line

    # Seed: the Gosper glider gun in the top-left, a pulsar off to the side.
    seed: set[Cell] = set()
    for dr, dc, name in [(2, 2, "gosper-glider-gun"), (rows - 8, cols - 16, "pulsar")]:
        for r, c in parse(PATTERNS[name]):
            seed.add((dr + r, dc + c))

    gen = 0
    try:
        while True:
            clear()
            sys.stdout.write(render(seed, gen, cols, rows))
            sys.stdout.flush()
            seed = step(seed)
            gen += 1
            time.sleep(0.08)
    except KeyboardInterrupt:
        clear()
        sys.stdout.write(f"stopped after {gen} generations\n")
        sys.stdout.flush()


if __name__ == "__main__":
    main()
