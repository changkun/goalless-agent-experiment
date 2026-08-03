"""Console entry point: ``python -m snake_game``."""

import argparse
import curses
import sys

from .ui import run


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(
        prog="snake",
        description="A dependency-free terminal snake game.",
    )
    parser.add_argument("--width", type=int, default=24, help="board width in cells")
    parser.add_argument("--height", type=int, default=20, help="board height in cells")
    parser.add_argument("--seed", type=int, default=None, help="RNG seed for reproducible food")
    parser.add_argument("--version", action="version", version="snake 1.0.0")
    args = parser.parse_args(argv)

    try:
        score = curses.wrapper(run, args.width, args.height, args.seed)
    except curses.error:
        print("This game needs a real terminal (curses failed to start).", file=sys.stderr)
        return 1

    if score >= 0:
        print(f"\nThanks for playing! Final score: {score}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
