"""Terminal entry point for the 2048 game."""

from __future__ import annotations

import argparse
import os
import random
import sys
from typing import Iterable

from .core import Board, Direction

# ANSI color mapping for tile values.
_COLORS = {
    0: "\x1b[0m",
    2: "\x1b[38;5;231;48;5;240m",
    4: "\x1b[38;5;231;48;5;59m",
    8: "\x1b[38;5;16;48;5;222m",
    16: "\x1b[38;5;16;48;5;220m",
    32: "\x1b[38;5;16;48;5;208m",
    64: "\x1b[38;5;16;48;5;202m",
    128: "\x1b[38;5;231;48;5;196m",
    256: "\x1b[38;5;231;48;5;160m",
    512: "\x1b[38;5;231;48;5;124m",
    1024: "\x1b[38;5;231;48;5;89m",
    2048: "\x1b[38;5;231;48;5;93m",
}
_RESET = "\x1b[0m"

_KEYS = {
    "w": Direction.UP,
    "a": Direction.LEFT,
    "s": Direction.DOWN,
    "d": Direction.RIGHT,
}


def _color(value: int) -> str:
    return _COLORS.get(value, "\x1b[38;5;231;48;5;52m")


def render(board: Board) -> list[str]:
    """Return the colored board as lines of text."""
    lines: list[str] = []
    for row in board.grid:
        cells = [f"{_color(v)} {v:>4} {_RESET}" for v in row]
        lines.append(" ".join(cells))
    return lines


def _read_key() -> str:
    """Read a single keypress from the terminal."""
    import termios
    import tty

    fd = sys.stdin.fileno()
    old = termios.tcgetattr(fd)
    try:
        tty.setraw(fd)
        ch = sys.stdin.read(1)
    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, old)
    return ch


def play(board: Board, target: int = 2048) -> None:
    print("\x1b[?25l", end="", flush=True)  # hide cursor
    try:
        while True:
            os.system("clear" if os.name == "posix" else "cls")
            print(f"Score: {board.score}   Highest: {board.max_tile()}")
            for line in render(board):
                print(line)
            print("\n[W/A/S/D] move  [Q] quit")

            if board.is_won(target) and not getattr(board, "_won_notice", False):
                print(f"\n🎉 You reached {target}!")
                board._won_notice = True

            if not board.can_move():
                print("\n💀 No moves left. Game over!")
                print(f"Final score: {board.score}")
                input("Press Enter to exit...")
                break

            key = _read_key().lower()
            if key in ("q", "\x1b"):
                break
            direction = _KEYS.get(key)
            if direction is None:
                continue
            result = board.move(direction)
            if not result.moved:
                print(" That move doesn't change anything.")
                input("Press Enter to continue...")
    finally:
        print("\x1b[?25h", end="", flush=True)  # restore cursor


def _parse_args(argv: Iterable[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="2048", description="Play 2048 in the terminal."
    )
    parser.add_argument("--size", type=int, default=4, help="board size (default: 4)")
    parser.add_argument(
        "--target", type=int, default=2048, help="winning tile (default: 2048)"
    )
    parser.add_argument(
        "--seed", type=int, default=None, help="random seed for reproducibility"
    )
    return parser.parse_args(list(argv))


def main(argv: Iterable[str] | None = None) -> int:
    args = _parse_args(argv if argv is not None else sys.argv[1:])
    board = Board(size=args.size, rng=random.Random(args.seed) if args.seed else None)
    play(board, target=args.target)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
