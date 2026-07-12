"""Command line interface for running Conway's Game of Life."""

from __future__ import annotations

import argparse
import shutil
import sys
import time

from .life import Board
from .patterns import PATTERNS


def _clear_screen() -> None:
    sys.stdout.write("\033[H\033[J")


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="gameoflife",
        description="Run Conway's Game of Life in your terminal.",
    )
    parser.add_argument(
        "--pattern",
        choices=sorted(PATTERNS),
        default="glider",
        help="Starting pattern to seed the board with.",
    )
    parser.add_argument(
        "--generations",
        type=int,
        default=50,
        help="Number of generations to simulate.",
    )
    parser.add_argument(
        "--interval",
        type=float,
        default=0.15,
        help="Seconds to pause between generations.",
    )
    parser.add_argument(
        "--padding",
        type=int,
        default=2,
        help="Extra dead cells to render around the live region.",
    )
    parser.add_argument(
        "--no-clear",
        action="store_true",
        help="Do not clear the screen between frames (prints a scrolling log).",
    )
    return parser


def run(argv=None) -> int:
    parser = build_arg_parser()
    args = parser.parse_args(argv)

    board = Board.from_pattern(PATTERNS[args.pattern])

    for _ in range(args.generations + 1):
        if not args.no_clear:
            _clear_screen()

        columns = shutil.get_terminal_size(fallback=(80, 24)).columns
        header = f"Generation {board.generation} | live cells: {len(board)}"
        print(header)
        print("-" * min(len(header), columns))
        rendering = board.render(padding=args.padding)
        print(rendering if rendering else "(empty board)")

        if board.generation >= args.generations:
            break

        time.sleep(args.interval)
        board = board.step()

    return 0


def main() -> None:
    raise SystemExit(run())


if __name__ == "__main__":
    main()
