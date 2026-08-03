"""Interactive terminal front end for the 2048 game."""

import argparse
import os
import sys

from game import Direction, Game


def clear_screen():
    os.system("cls" if os.name == "nt" else "clear")


def read_key():
    """Read a single keypress without requiring Enter."""
    try:
        import termios
        import tty
    except ImportError:  # Windows fallback
        return input().strip() or ""

    fd = sys.stdin.fileno()
    old = termios.tcgetattr(fd)
    try:
        tty.setraw(fd)
        ch = sys.stdin.read(1)
        # Detect arrow-key escape sequences (^[[A etc.)
        if ch == "\x1b":
            seq = sys.stdin.read(2)
            ch = "up" if seq == "[A" else "down" if seq == "[B" else \
                 "left" if seq == "[D" else "right" if seq == "[C" else ch
        return ch
    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, old)


def main(argv=None):
    parser = argparse.ArgumentParser(
        description="Play 2048 in your terminal.")
    parser.add_argument("--size", type=int, default=4,
                        help="board size (default 4)")
    parser.add_argument("--seed", type=int, default=None,
                        help="seed the random generator for reproducible games")
    args = parser.parse_args(argv)

    if args.size < 2:
        parser.error("--size must be at least 2")

    rng = __import__("random").Random(args.seed) if args.seed else None
    game = Game(size=args.size, rng=rng)

    clear_screen()
    while True:
        print(game.render())
        print(game.status())
        print("Keys: WASD or arrow keys, q to quit")
        key = read_key()

        if key in ("q", "Q", "\x03"):
            print("\nThanks for playing!")
            return 0

        direction = Direction.resolve(key)
        if direction:
            before = game.copy()
            game.move(direction)
            if game.board == before.board:
                print("That move didn't change anything.")
                continue
            clear_screen()

        if game.over or game.won:
            clear_screen()
            print(game.render())
            print(game.status())
            while True:
                again = input("Play again? (y/n): ").strip().lower()
                if again in ("y", "yes"):
                    game = Game(rng=game.rng)
                    clear_screen()
                    break
                if again in ("n", "no"):
                    print("Thanks for playing!")
                    return 0
    return 0


if __name__ == "__main__":
    import random
    sys.exit(main())
