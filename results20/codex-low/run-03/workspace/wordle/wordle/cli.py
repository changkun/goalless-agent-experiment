"""Terminal UI for the Wordle game, using only the standard library."""

import argparse
import sys

from .game import MAX_GUESSES, GREEN, GRAY, Wordle, YELLOW

RESET = "\033[0m"
BOLD = "\033[1m"
_COLORS = {
    GREEN: "\033[48;5;28m",
    YELLOW: "\033[48;5;214m",
    GRAY: "\033[48;5;240m",
}


def _paint(letter: str, color: str) -> str:
    bg = _COLORS.get(color, "")
    return f"{bg}{BOLD} {letter} {RESET}"


def draw_guesses(game: Wordle) -> str:
    """Render the board: played guesses plus blank rows."""
    lines = []
    for idx in range(MAX_GUESSES):
        if idx < len(game.guesses):
            word = game.guesses[idx]
            pattern = game.patterns[idx]
            lines.append("  " + " ".join(_paint(word[i], pattern[i]) for i in range(5)))
        else:
            lines.append("  " + " ".join("   " for _ in range(5)))
    return "\n".join(lines)


def _read_guess(prompt: str) -> str:
    if sys.stdin.isatty():
        return input(prompt).strip()
    return sys.stdin.readline().strip()


def play(answer: str = None) -> bool:
    """Run one round. Returns True if the player won."""
    game = Wordle(answer)
    print(f"\n{BOLD}  WORDLE{RESET}  (5 letters, 6 guesses)\n")

    while not game.finished:
        print(draw_guesses(game))
        print()
        prompt = f"  Guess {len(game.guesses) + 1}/{MAX_GUESSES}: "
        guess = _read_guess(prompt).strip().upper()

        if guess in ("Q", "QUIT", "EXIT"):
            print(f"\n  The answer was: {game.answer}\n")
            return False

        err = game.validate(guess)
        if err:
            print("  " + err)
            continue

        game.guess(guess)
        if game.won:
            print(draw_guesses(game))
            print(f"\n  {BOLD}You got it in {len(game.guesses)} guesses!{RESET}\n")
            return True

    print(draw_guesses(game))
    print(f"\n  {BOLD}Out of guesses. The word was {game.answer}.{RESET}\n")
    return False


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="Play Wordle in your terminal.")
    parser.add_argument("--answer", help="Set a specific answer (for testing).")
    args = parser.parse_args(argv)

    answer = None
    if args.answer:
        answer = args.answer.upper()
        if len(answer) != 5 or not answer.isalpha():
            print("Answer must be a 5-letter word.", file=sys.stderr)
            return 1

    try:
        play(answer)
    except (KeyboardInterrupt, EOFError):
        print()
        return 0
    return 0


if __name__ == "__main__":
    sys.exit(main())
