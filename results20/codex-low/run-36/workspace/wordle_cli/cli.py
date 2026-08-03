"""Interactive command-line interface for the Wordle clone."""

import random
import sys
from typing import List, Optional

from game import Feedback, Wordle, format_feedback, is_correct, score_guess

WORDLIST = [
    "APPLE", "BRAVE", "CRANE", "DOGMA", "EAGLE", "FIGHT", "GHOST",
    "HOUSE", "IGLOO", "JUMPY", "KOALA", "LEMON", "MANGO", "NIGHT",
    "OCEAN", "PIANO", "QUEEN", "RIVER", "STORM", "TIGER", "UNITY",
    "VIVID", "WALTZ", "XENON", "YACHT", "ZEBRA",
]


def _valid_word(word: str, max_guesses: int) -> Optional[Wordle]:
    try:
        return Wordle.from_word(word, max_guesses=max_guesses)
    except ValueError:
        return None


def run(answer: Optional[str] = None, max_guesses: int = 6) -> bool:
    """Run one game. Returns True if the player won."""
    if answer is None:
        answer = random.choice(WORDLIST)
    game = _valid_word(answer, max_guesses)
    if game is None:
        print(f"Invalid answer: {answer!r}", file=sys.stderr)
        return False

    remaining = [w for w in WORDLIST if w != game.answer]
    print(f"Guess the 5-letter word! ({game.max_guesses} tries)\n")

    for attempt in range(game.max_guesses):
        guess = input("> ").strip().upper()
        if len(guess) != 5 or not guess.isalpha():
            print("  Please enter a 5-letter word.")
            continue
        if guess.lower() not in [w.lower() for w in remaining] and guess != game.answer:
            print("  Not in the word list.")
            continue

        feedback = score_guess(guess, game.answer)
        print(f"  {format_feedback(feedback)}")

        if is_correct(feedback):
            print(f"\nYou won in {attempt + 1} tries!")
            return True

    print(f"\nOut of tries! The word was {game.answer}.")
    return False


def main() -> None:
    """Entry point for the CLI."""
    args = sys.argv[1:]
    fixed = None
    max_guesses = 6
    i = 0
    while i < len(args):
        if args[i] == "--answer" and i + 1 < len(args):
            fixed = args[i + 1]
            i += 2
        elif args[i] == "--guesses" and i + 1 < len(args):
            try:
                max_guesses = int(args[i + 1])
            except ValueError:
                print("--guesses must be an integer", file=sys.stderr)
                return
            i += 2
        elif args[i] in ("-h", "--help"):
            print("Usage: cli.py [--answer WORD] [--guesses N]")
            return
        else:
            print(f"Unknown option: {args[i]}", file=sys.stderr)
            return

    won = run(fixed, max_guesses=max_guesses)
    sys.exit(0 if won else 1)


if __name__ == "__main__":
    main()
