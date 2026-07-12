"""Terminal animation runner for Conway's Game of Life."""

from __future__ import annotations

import argparse
import sys
import time

from .board import Board
from .patterns import PATTERNS


def _clear_screen() -> None:
    sys.stdout.write("\x1b[H\x1b[J")


def run(board: Board, generations: int, delay: float) -> None:
    for gen in range(generations):
        _clear_screen()
        print(f"Generation {gen}  (live cells: {len(board)})")
        print(board.render() or "(empty)")
        if len(board) == 0:
            break
        board = board.step()
        time.sleep(delay)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="gol",
        description="Animate Conway's Game of Life in the terminal.",
    )
    parser.add_argument(
        "pattern",
        choices=sorted(PATTERNS),
        default="glider",
        nargs="?",
        help="Starting pattern to simulate (default: glider).",
    )
    parser.add_argument(
        "-g",
        "--generations",
        type=int,
        default=60,
        help="Number of generations to simulate (default: 60).",
    )
    parser.add_argument(
        "-d",
        "--delay",
        type=float,
        default=0.1,
        help="Delay in seconds between generations (default: 0.1).",
    )
    return parser


def main(argv: list[str] | None = None) -> None:
    args = build_parser().parse_args(argv)
    board = Board.from_pattern(PATTERNS[args.pattern])
    try:
        run(board, args.generations, args.delay)
    except KeyboardInterrupt:
        print("\nStopped.")


if __name__ == "__main__":
    main()
