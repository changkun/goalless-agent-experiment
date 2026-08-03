"""Command-line entry point for the Wordle clone."""
import argparse
import sys

from wordle_cli.game import Game
from wordle_cli.stats import record
from wordle_cli.words import random_word


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="wordle",
        description="Play a word-guessing game in your terminal.",
    )
    parser.add_argument(
        "--word", type=str, default=None,
        help="Use a specific secret word (for testing/demos).",
    )
    parser.add_argument(
        "--no-color", action="store_true",
        help="Disable ANSI colors in output.",
    )
    parser.add_argument(
        "--max-attempts", type=int, default=6,
        help="Number of attempts allowed (default: 6).",
    )
    return parser


def main(argv=None) -> int:
    args = build_parser().parse_args(argv)
    secret = (args.word or random_word()).lower()
    game = Game(secret=secret, max_attempts=args.max_attempts)

    def out(message: str) -> None:
        print(message)

    won = game.play(input_fn=input, output_fn=out, colors=not args.no_color)
    record({"won": won, "attempts": len(game.guesses)})
    return 0 if won else 1


if __name__ == "__main__":
    sys.exit(main())
