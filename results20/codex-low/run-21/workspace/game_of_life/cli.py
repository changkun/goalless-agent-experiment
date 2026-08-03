"""Command-line interface for the Game of Life."""

from __future__ import annotations

import argparse
import os
import sys
import time

from .engine import Board, parse_rle
from .patterns import PATTERNS, get_board
from .render import render


def _build_board(pattern: str | None) -> Board:
    if pattern is None or pattern == "blinker":
        return get_board("blinker")
    if pattern in PATTERNS:
        return get_board(pattern)
    # Treat unknown input as raw RLE text.
    return parse_rle(pattern)


def _loop(board: Board, args: argparse.Namespace) -> int:
    try:
        for generation in range(args.generations):
            frame = render(board)
            tag = f"gen {generation} | population {board.population()}"
            if frame:
                sys.stdout.write(f"{tag}\n{frame}\n")
            else:
                sys.stdout.write(f"{tag} (extinct)\n")
            if args.interval and generation < args.generations - 1:
                time.sleep(args.interval)
            else:
                sys.stdout.write("\n")
            sys.stdout.flush()
            board.step()
    except BrokenPipeError:
        # Downstream reader (e.g. `head` or `less`) closed the pipe.
        devnull = os.open(os.devnull, os.O_WRONLY)
        os.dup2(devnull, sys.stdout.fileno())
        return 0
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="game-of-life",
        description="Simulate Conway's Game of Life and print generations.",
    )
    parser.add_argument(
        "pattern",
        nargs="?",
        help="Built-in pattern name or raw RLE body (default: blinker).",
    )
    parser.add_argument(
        "-n", "--generations",
        type=int,
        default=5,
        help="Number of generations to simulate (default: 5).",
    )
    parser.add_argument(
        "-i", "--interval",
        type=float,
        default=0.0,
        help="Seconds to pause between frames (default: 0).",
    )
    args = parser.parse_args(argv)

    if args.generations < 1:
        print("generations must be >= 1", file=sys.stderr)
        return 2

    board = _build_board(args.pattern)
    return _loop(board, args)


if __name__ == "__main__":
    raise SystemExit(main())
