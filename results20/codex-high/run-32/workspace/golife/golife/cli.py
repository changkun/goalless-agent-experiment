"""Command-line interface for golife."""
from __future__ import annotations

import argparse
import os
import random
import sys
import time
from typing import Sequence

from .engine import Universe
from .patterns import get, list_patterns, PATTERNS


def _read_stdin() -> str:
    return sys.stdin.read()


def _parse_pattern_text(text: str) -> set[tuple[int, int]]:
    cells: set[tuple[int, int]] = set()
    for y, line in enumerate(text.splitlines()):
        for x, ch in enumerate(line):
            if ch in ("*", "O", "#", "o"):
                cells.add((x, y))
    return cells


def run_simulation(
    universe: Universe,
    generations: int,
    width: int | None,
    height: int | None,
    delay: float,
) -> None:
    for gen in range(generations):
        if width is None and height is None:
            page = universe.render()
        else:
            page = universe.render(width=width, height=height)
        sys.stdout.write("\033[H\033[2J")  # move home + clear
        sys.stdout.write(f"generation {gen}  population {universe.population}\n")
        sys.stdout.write(page)
        sys.stdout.write("\n")
        sys.stdout.flush()
        time.sleep(delay)
        universe.step()


def _display_names() -> str:
    return ", ".join(list_patterns())


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="golife",
        description="Conway's Game of Life in your terminal.",
    )
    parser.add_argument(
        "pattern",
        nargs="?",
        default="glider",
        help=f"starting pattern ({_display_names()}) or '-' to read from stdin",
    )
    parser.add_argument(
        "-g", "--generations", type=int, default=50,
        help="number of generations to run (default: 50)",
    )
    parser.add_argument(
        "-d", "--delay", type=float, default=0.1,
        help="seconds between frames in interactive mode (default: 0.1)",
    )
    parser.add_argument(
        "-n", "--nongui", action="store_true",
        help="print final frame only, without animation",
    )
    parser.add_argument(
        "-w", "--width", type=int, default=None,
        help="rendered width in columns",
    )
    parser.add_argument(
        "-H", "--height", type=int, default=None,
        help="rendered height in rows",
    )
    parser.add_argument(
        "-r", "--random", action="store_true",
        help="start from a random soup instead of a named pattern",
    )
    parser.add_argument(
        "--seed", type=int, default=None,
        help="random seed for the -r soup",
    )
    parser.add_argument(
        "--list", action="store_true",
        help="list available patterns and exit",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.list:
        for name in list_patterns():
            print(name)
        return 0

    universe = Universe()

    if args.random:
        rng = random.Random(args.seed)
        w = args.width or 40
        h = args.height or 20
        cells = {
            (x, y)
            for x in range(w)
            for y in range(h)
            if rng.random() < 0.25
        }
        universe = Universe(cells)
    elif args.pattern == "-":
        universe = Universe(_parse_pattern_text(_read_stdin()))
    else:
        pattern = get(args.pattern)
        universe = Universe(pattern.cells())

    if args.generations < 1:
        print(universe.render(width=args.width, height=args.height))
        return 0

    if args.nongui or "--nongui" in (argv or []):
        universe.step(args.generations - 1)
        out = universe.render(width=args.width, height=args.height)
        print(out)
        return 0

    run_simulation(
        universe, args.generations, args.width, args.height, args.delay
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
