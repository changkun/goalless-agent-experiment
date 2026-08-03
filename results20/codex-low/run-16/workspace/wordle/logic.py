"""Pure game logic for the Wordle clone. No I/O here so it's easy to test."""

from collections import Counter
from random import SystemRandom

from .words import WORDS

WORD_LENGTH = 5
MAX_GUESSES = 6

# Letter states
CORRECT = "correct"     # right letter, right place
PRESENT = "present"     # right letter, wrong place
ABSENT = "absent"       # letter not in the answer


def pick_word(words=None, rng=None):
    """Return a random answer word from the list."""
    source = list(words) if words is not None else WORDS
    rng = rng or SystemRandom()
    return rng.choice(source)


def is_valid_guess(guess):
    """A guess is valid if it is 5 lowercase letters."""
    return len(guess) == WORD_LENGTH and guess.isalpha() and guess.islower()


def evaluate(guess, answer):
    """
    Score a guess against the answer.

    Returns a list of letter states in order. A letter already consumed by an
    earlier exact match is not reported as present elsewhere.
    """
    if len(guess) != len(answer):
        raise ValueError("guess and answer must be the same length")

    # First pass: mark exact matches and tally remaining answer letters.
    result = [ABSENT] * len(guess)
    remaining = Counter()
    for i, (g, a) in enumerate(zip(guess, answer)):
        if g == a:
            result[i] = CORRECT
        else:
            remaining[a] += 1

    # Second pass: mark misplaced letters that still have budget.
    for i, (g, a) in enumerate(zip(guess, answer)):
        if result[i] == CORRECT:
            continue
        if remaining.get(g, 0) > 0:
            result[i] = PRESENT
            remaining[g] -= 1

    return result


def is_win(result):
    """True when every letter scored as correct."""
    return all(state == CORRECT for state in result)


def colorize(letter, state):
    """Map a letter and its state to a small ANSI colored string."""
    ansi = {
        CORRECT: "\033[30;42m",   # black on green
        PRESENT: "\033[30;43m",   # black on yellow
        ABSENT: "\033[30;47m",    # black on white
    }
    reset = "\033[0m"
    return f"{ansi[state]}{letter}{reset}"
