"""Core Wordle game logic: state, validation, and color feedback."""
from __future__ import annotations

import dataclasses
import random
from datetime import date
from typing import List, Optional, Sequence

from .words import VALID_WORDS

MAX_GUESSES = 6
WORD_LEN = 5

GREEN = "green"
YELLOW = "yellow"
GREY = "grey"


@dataclasses.dataclass
class GuessResult:
    """Feedback for a single guess: one color code per letter."""

    colors: List[str]
    is_correct: bool = False


def random_word(rng: Optional[random.Random] = None) -> str:
    rng = rng or random
    return rng.choice(VALID_WORDS)


def daily_word(day: Optional[date] = None) -> str:
    """A deterministic word derived from the date (stable across runs)."""
    day = day or date.today()
    seed = day.toordinal()
    return VALID_WORDS[seed % len(VALID_WORDS)]


def is_valid(guess: str) -> bool:
    return guess in VALID_WORDS


def score(guess: str, answer: str) -> GuessResult:
    """Grade a guess against the answer using Wordle's exact rules.

    A letter already matched green is taken out of the pool so duplicate
    letters behave correctly (a second occurrence only yields yellow if the
    answer actually has another one left).
    """
    if len(guess) != len(answer):
        raise ValueError("guess and answer must be the same length")

    colors = [GREY] * len(answer)
    remaining = list(answer)

    # First pass: mark exact matches and remove them from the pool.
    for i, (g, a) in enumerate(zip(guess, answer)):
        if g == a:
            colors[i] = GREEN
            remaining[i] = None

    # Second pass: mark misplaced matches against remaining letters.
    for i, g in enumerate(guess):
        if colors[i] != GREY:
            continue
        for j, r in enumerate(remaining):
            if r is not None and r == g:
                colors[i] = YELLOW
                remaining[j] = None
                break

    return GuessResult(colors=colors, is_correct=guess == answer)


class Game:
    """Holds all game state and exposes progress in a purely testable way."""

    def __init__(self, answer: str, max_guesses: int = MAX_GUESSES):
        if len(answer) != WORD_LEN:
            raise ValueError(f"answer must be {WORD_LEN} letters")
        self.answer = answer.lower()
        self.max_guesses = max_guesses
        self.guesses: List[GuessResult] = []

    @property
    def guesses_left(self) -> int:
        return max(0, self.max_guesses - len(self.guesses))

    @property
    def won(self) -> bool:
        return bool(self.guesses) and self.guesses[-1].is_correct

    @property
    def over(self) -> bool:
        return self.won or self.guesses_left == 0

    def submit(self, guess: str) -> GuessResult:
        """Validate and record a guess, returning its feedback."""
        guess = guess.lower()
        if not is_valid(guess):
            raise ValueError(f"'{guess}' is not a valid 5-letter word")
        if self.over:
            raise ValueError("game is already over")
        result = score(guess, self.answer)
        self.guesses.append(result)
        return result

    def remaining_valid_guesses(self) -> Sequence[str]:
        return VALID_WORDS
