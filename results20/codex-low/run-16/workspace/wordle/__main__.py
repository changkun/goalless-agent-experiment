"""Command-line interface for the Wordle clone."""

import argparse
import sys

from . import logic
from .words import WORDS


def build_parser():
    parser = argparse.ArgumentParser(
        prog="wordle",
        description="Play a terminal Wordle game.",
    )
    parser.add_argument(
        "-n", "--guesses", type=int, default=logic.MAX_GUESSES,
        help=f"number of allowed guesses (default: {logic.MAX_GUESSES})",
    )
    parser.add_argument(
        "--no-color", action="store_true",
        help="disable ANSI colors in the output",
    )
    parser.add_argument(
        "--answer", help="force a specific answer (only lowercase letters)",
    )
    return parser


def render_guess(guess, result, color):
    """Render a single guess row."""
    if color:
        row = " ".join(
            logic.colorize(letter, state)
            for letter, state in zip(guess, result)
        )
    else:
        glyphs = {
            logic.CORRECT: "G",
            logic.PRESENT: "Y",
            logic.ABSENT: ".",
        }
        row = guess + "  " + "".join(glyphs[s] for s in result)
    return row


def prompt_guess(valid_words):
    """Loop until the player types a valid guess."""
    while True:
        raw = input("Guess: ").strip().lower()
        if not logic.is_valid_guess(raw):
            print("Please enter exactly 5 lowercase letters.")
            continue
        if raw not in valid_words:
            print("That's not in the word list. Try again.")
            continue
        return raw


def run(args, valid_words, answer, out):
    """Play one full game, printing output to `out`. Returns win boolean."""
    color = not args.no_color
    for attempt in range(args.guesses):
        guess = prompt_guess(valid_words)
        result = logic.evaluate(guess, answer)
        print(render_guess(guess, result, color), file=out)
        if logic.is_win(result):
            print(f"\nYou got it in {attempt + 1} guess(es)!", file=out)
            return True
    print(f"\nOut of guesses. The word was {answer.upper()}.", file=out)
    return False


def main(argv=None):
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.answer:
        answer = args.answer.lower()
        if not logic.is_valid_guess(answer):
            parser.error("--answer must be exactly 5 lowercase letters")
    else:
        answer = logic.pick_word()

    if args.guesses < 1:
        parser.error("-n/--guesses must be at least 1")

    print("Welcome to Wordle! Guess the 5-letter word.", file=sys.stdout)
    run(args, set(WORDS), answer, sys.stdout)


if __name__ == "__main__":
    main()
