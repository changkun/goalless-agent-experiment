"""Interactive terminal entry point for wordle_cli."""
from __future__ import annotations

import argparse
import random
import sys

from . import __version__
from .game import WORD_LEN, Game, daily_word, random_word

# ANSI color codes (only used when stdout is a TTY).
_GREEN = "\033[1;32m"
_YELLOW = "\033[1;33m"
_GREY = "\033[1;30m"
_RESET = "\033[0m"


def _colored(letter: str, color: str, use_color: bool) -> str:
    if not use_color:
        return letter
    code = {"green": _GREEN, "yellow": _YELLOW, "grey": _GREY}[color]
    return f"{code}{letter}{_RESET}"


def _glyph(color: str) -> str:
    return {"green": "🟩", "yellow": "🟨", "grey": "⬜"}[color]


def _render(guess: str, colors, use_color: bool) -> str:
    if use_color:
        letters = " ".join(_colored(c, col, True) for c, col in zip(guess, colors))
        return letters + "  " + "".join(_glyph(col) for col in colors)
    return " ".join(_glyph(col) for col in colors)


def play(answer: str, guess_fn=None, use_color: bool = None) -> Game:
    """Run one game. `guess_fn` overrides stdin for tests/scripts."""
    if use_color is None:
        use_color = sys.stdout.isatty()
    game = Game(answer)
    prompt = "Guess a 5-letter word: "

    while not game.over:
        guess = None
        while guess is None:
            try:
                raw = (guess_fn() if guess_fn else input(prompt)).strip().lower()
            except EOFError:
                print()
                print(f"Quit. The word was {game.answer}.")
                return game
            if len(raw) != WORD_LEN or not raw.isalpha():
                print(f"Please enter a {WORD_LEN}-letter word.")
                continue
            try:
                result = game.submit(raw)
            except ValueError as exc:
                print(str(exc))
                continue
            guess = raw

        print(_render(guess, result.colors, use_color))
        if result.is_correct:
            print(f"Won in {len(game.guesses)} guesses! 🎉")
            return game

    print(f"Out of guesses. The word was {game.answer}.")
    return game


def _build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="wordle", description="Play Wordle in your terminal.")
    mode = p.add_mutually_exclusive_group()
    mode.add_argument("--daily", action="store_true", help="play the word for today's date")
    mode.add_argument("--word", metavar="ANSWER", help="play with a specific hidden word")
    mode.add_argument("--list-words", action="store_true", help="print all valid words and exit")
    p.add_argument("--no-color", action="store_true", help="disable ANSI colors")
    p.add_argument("--version", action="version", version=f"wordle {__version__}")
    return p


def main(argv=None) -> int:
    args = _build_parser().parse_args(argv)
    if args.list_words:
        from .words import VALID_WORDS
        print("\n".join(VALID_WORDS))
        return 0

    if args.word:
        answer = args.word.strip().lower()
        if len(answer) != WORD_LEN or not answer.isalpha():
            print(f"answer must be a {WORD_LEN}-letter word", file=sys.stderr)
            return 2
    elif args.daily:
        answer = daily_word()
    else:
        answer = random_word()

    use_color = not args.no_color
    play(answer, use_color=use_color)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
