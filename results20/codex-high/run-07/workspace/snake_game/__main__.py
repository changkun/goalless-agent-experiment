"""Run the game directly with: python -m snake_game"""

import argparse

from snake_game.ui import play


def main(argv=None):
    parser = argparse.ArgumentParser(description="Play Snake in your terminal.")
    parser.add_argument("--width", type=int, default=20, help="Board width")
    parser.add_argument("--height", type=int, default=10, help="Board height")
    parser.add_argument("--seed", type=int, default=None, help="Random seed for food placement")
    args = parser.parse_args(argv)
    play(args.width, args.height, args.seed)


if __name__ == "__main__":
    main()
