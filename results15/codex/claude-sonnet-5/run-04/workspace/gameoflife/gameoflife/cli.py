"""Command-line runner that animates a Game of Life board in the terminal."""

from __future__ import annotations

import argparse
import sys
import time

from .life import Board

GLIDER = """
.#.
..#
###
"""

PULSAR = """
......#.....#......
......#.....#......
......##...##......
....................
#....##.....##....#
###.#.##...##.#.###
...##.#######.##...
......###.###......
......#.....#......
......##...##......
......#.....#......
...##.#######.##...
###.#.##...##.#.###
#....##.....##....#
....................
......##...##......
......#.....#......
......#.....#......
"""

PRESETS = {
    "glider": GLIDER,
    "pulsar": PULSAR,
}


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Play Conway's Game of Life in the terminal.")
    parser.add_argument(
        "--preset",
        choices=sorted(PRESETS),
        default="glider",
        help="Starting pattern to use (default: glider).",
    )
    parser.add_argument(
        "--file",
        help="Path to a text file containing a pattern ('#' alive, anything else dead).",
    )
    parser.add_argument(
        "--generations",
        type=int,
        default=40,
        help="Number of generations to simulate (default: 40).",
    )
    parser.add_argument(
        "--interval",
        type=float,
        default=0.2,
        help="Seconds to pause between generations (default: 0.2).",
    )
    parser.add_argument(
        "--padding",
        type=int,
        default=2,
        help="Extra dead cells to render around the bounding box (default: 2).",
    )
    return parser.parse_args(argv)


def load_board(args: argparse.Namespace) -> Board:
    if args.file:
        with open(args.file, "r", encoding="utf-8") as handle:
            pattern = handle.read()
    else:
        pattern = PRESETS[args.preset]
    return Board.from_pattern(pattern)


def run(argv: list[str] | None = None) -> None:
    args = parse_args(argv)
    board = load_board(args)

    for generation in range(args.generations + 1):
        sys.stdout.write("\x1b[2J\x1b[H")
        print(f"Generation {generation} — population {board.population()}")
        print(board.render(padding=args.padding))
        sys.stdout.flush()

        if board.population() == 0:
            print("\nAll cells are dead. Stopping early.")
            break

        if generation < args.generations:
            time.sleep(args.interval)
            board = board.step()


def main() -> None:
    try:
        run()
    except KeyboardInterrupt:
        print("\nStopped.")


if __name__ == "__main__":
    main()
