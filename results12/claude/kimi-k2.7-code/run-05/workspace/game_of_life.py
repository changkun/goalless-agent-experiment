#!/usr/bin/env python3
"""
Conway's Game of Life in the terminal.

A zero-player cellular automaton: cells live, die, or are born based on
their neighbors. This implementation runs in the terminal with a few
built-in starting patterns and a simple command-line interface.
"""

import argparse
import copy
import os
import sys
import time
from typing import List, Set, Tuple


# A "living" cell is stored as a (row, col) tuple in a set.
Grid = Set[Tuple[int, int]]


def neighbors(row: int, col: int) -> List[Tuple[int, int]]:
    """Return the eight neighboring coordinates of a cell."""
    return [
        (row + dr, col + dc)
        for dr in (-1, 0, 1)
        for dc in (-1, 0, 1)
        if not (dr == 0 and dc == 0)
    ]


def step(living: Grid) -> Grid:
    """Advance the simulation by one generation."""
    candidate_counts: dict[Tuple[int, int], int] = {}

    for cell in living:
        for n in neighbors(*cell):
            candidate_counts[n] = candidate_counts.get(n, 0) + 1

    next_generation: Grid = set()

    for cell, count in candidate_counts.items():
        if count == 3 or (count == 2 and cell in living):
            next_generation.add(cell)

    return next_generation


def bounding_box(living: Grid) -> Tuple[int, int, int, int]:
    """Return (min_row, min_col, max_row, max_col) for the living cells."""
    if not living:
        return 0, 0, 0, 0
    rows = {r for r, _ in living}
    cols = {c for _, c in living}
    return min(rows), min(cols), max(rows), max(cols)


def render(living: Grid, rows: int, cols: int) -> str:
    """Render the grid centered in a rows x cols viewport."""
    if not living:
        return "\n".join([" " * cols] * rows)

    min_r, min_c, max_r, max_c = bounding_box(living)
    height = max_r - min_r + 1
    width = max_c - min_c + 1

    # Center the pattern in the viewport.
    pad_top = max(0, (rows - height) // 2)
    pad_left = max(0, (cols - width) // 2)

    lines = [" " * cols for _ in range(rows)]
    for r, c in living:
        y = r - min_r + pad_top
        x = c - min_c + pad_left
        if 0 <= y < rows and 0 <= x < cols:
            line = list(lines[y])
            line[x] = "█"
            lines[y] = "".join(line)

    return "\n".join(lines)


def parse_pattern(text: str) -> Grid:
    """Parse a multiline string where 'O' marks a live cell."""
    living: Grid = set()
    for r, line in enumerate(text.strip("\n").splitlines()):
        for c, ch in enumerate(line):
            if ch in "OoXx#█":
                living.add((r, c))
    return living


# A small library of classic patterns.
PATTERNS = {
    "random": None,  # handled specially
    "glider": parse_pattern(
        """
        .O.
        ..O
        OOO
        """
    ),
    "blinker": parse_pattern(
        """
        OOO
        """
    ),
    "beacon": parse_pattern(
        """
        OO..
        OO..
        ..OO
        ..OO
        """
    ),
    "toad": parse_pattern(
        """
        .OOO
        OOO.
        """
    ),
    "rpentomino": parse_pattern(
        """
        .OO
        OO.
        .O.
        """
    ),
    "gosper": parse_pattern(
        """
        ........................O...........
        ......................O.O...........
        ............OO......OO............OO
        ...........O...O....OO............OO
        OO........O.....O...OO..............
        OO........O...O.OO....O.O...........
        ..........O.....O.......O...........
        ...........O...O....................
        ............OO......................
        """
    ),
    "diehard": parse_pattern(
        """
        .......O
        OO......
        .O...OOO
        """
    ),
}


def random_grid(rows: int, cols: int, density: float = 0.25) -> Grid:
    """Create a random grid with the given cell density."""
    import random

    living: Grid = set()
    for r in range(rows):
        for c in range(cols):
            if random.random() < density:
                living.add((r, c))
    return living


def get_terminal_size() -> Tuple[int, int]:
    """Return (rows, cols) of the terminal, falling back to a sane default."""
    try:
        cols, rows = os.get_terminal_size(sys.stdout.fileno())
    except OSError:
        rows, cols = 24, 80
    return rows, cols


def clear_screen() -> None:
    """Clear the terminal in a cross-platform way."""
    os.system("cls" if os.name == "nt" else "clear")


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Conway's Game of Life in the terminal.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="Available patterns:\n  "
        + "\n  ".join(sorted(PATTERNS.keys())),
    )
    parser.add_argument(
        "pattern",
        nargs="?",
        default="random",
        choices=sorted(PATTERNS.keys()),
        help="Starting pattern (default: random)",
    )
    parser.add_argument(
        "-d",
        "--density",
        type=float,
        default=0.25,
        help="Density for random pattern (0.0 - 1.0, default: 0.25)",
    )
    parser.add_argument(
        "-g",
        "--generations",
        type=int,
        default=None,
        help="Stop after N generations (default: run forever)",
    )
    parser.add_argument(
        "-s",
        "--speed",
        type=float,
        default=0.1,
        help="Seconds between generations (default: 0.1)",
    )
    parser.add_argument(
        "--no-clear",
        action="store_true",
        help="Print each frame rather than clearing the screen",
    )

    args = parser.parse_args()

    if args.density < 0.0 or args.density > 1.0:
        print("error: density must be between 0.0 and 1.0", file=sys.stderr)
        return 1

    term_rows, term_cols = get_terminal_size()

    # Use a slightly smaller viewport than the terminal to avoid line wrapping.
    rows = max(10, term_rows - 2)
    cols = max(20, term_cols - 2)

    if args.pattern == "random":
        living = random_grid(rows, cols, args.density)
    else:
        living = copy.deepcopy(PATTERNS[args.pattern])

    generation = 0
    try:
        while True:
            frame = render(living, rows, cols)
            if args.no_clear:
                print(f"Generation {generation}")
                print(frame)
                print("-" * cols)
            else:
                clear_screen()
                print(f"Generation {generation} — {args.pattern}")
                print(frame)

            living = step(living)
            generation += 1

            if args.generations is not None and generation >= args.generations:
                break

            time.sleep(args.speed)
    except KeyboardInterrupt:
        if not args.no_clear:
            clear_screen()
        print(f"Stopped at generation {generation}.")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
