"""Command line interface: ``python -m labyrinth``."""

from __future__ import annotations

import argparse
import random
import sys

from .generators import GENERATORS, braid
from .grid import Cell, Grid
from .render import RENDERERS
from .solvers import longest_path, shortest_path, stats


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="labyrinth",
        description="Generate, solve and render mazes in the terminal.",
    )
    parser.add_argument("-H", "--height", type=int, default=12, help="rows of cells")
    parser.add_argument("-W", "--width", type=int, default=24, help="columns of cells")
    parser.add_argument(
        "-a",
        "--algorithm",
        choices=sorted(GENERATORS),
        default="backtracker",
        help="carving algorithm",
    )
    parser.add_argument("-s", "--seed", type=int, help="seed for reproducible mazes")
    parser.add_argument(
        "-r",
        "--render",
        choices=sorted(RENDERERS),
        default="blocks",
        help="output style",
    )
    parser.add_argument(
        "--braid",
        type=float,
        default=0.0,
        metavar="RATIO",
        help="remove this fraction of dead ends to create loops (0-1)",
    )
    parser.add_argument(
        "--solve",
        action="store_true",
        help="mark the path from the top-left to the bottom-right cell",
    )
    parser.add_argument(
        "--longest",
        action="store_true",
        help="mark the longest path in the maze instead of corner to corner",
    )
    parser.add_argument("--stats", action="store_true", help="print maze metrics")
    return parser


def _solution(grid: Grid, args: argparse.Namespace) -> list[Cell] | None:
    if args.longest:
        return longest_path(grid)
    if args.solve:
        return shortest_path(grid, (0, 0), (grid.height - 1, grid.width - 1))
    return None


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.height < 1 or args.width < 1:
        print("height and width must be positive", file=sys.stderr)
        return 2
    if not 0.0 <= args.braid <= 1.0:
        print("--braid must be between 0 and 1", file=sys.stderr)
        return 2

    rng = random.Random(args.seed)
    grid = GENERATORS[args.algorithm](args.height, args.width, rng)
    if args.braid:
        braid(grid, rng, args.braid)

    print(RENDERERS[args.render](grid, _solution(grid, args)))

    if args.stats:
        print()
        for key, value in stats(grid).items():
            print(f"{key.replace('_', ' '):>15}: {value}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
