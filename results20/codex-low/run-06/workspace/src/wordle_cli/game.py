"""Core game logic for the Wordle clone.

Feedback for each letter of a guess is one of:
    GREEN  - in the secret and in the correct position
    YELLOW - in the secret but in the wrong position
    GRAY   - not in the secret
"""
from dataclasses import dataclass, field
from enum import Enum
from typing import List, Optional, Callable


class Feedback(Enum):
    GREEN = "G"
    YELLOW = "Y"
    GRAY = "X"


MAX_ATTEMPTS = 6


@dataclass
class Guess:
    word: str
    feedback: List[Feedback]


@dataclass
class Game:
    secret: str
    max_attempts: int = MAX_ATTEMPTS
    guesses: List[Guess] = field(default_factory=list)

    @property
    def is_won(self) -> bool:
        return bool(self.guesses) and self._all_green(self.guesses[-1])

    @property
    def is_over(self) -> bool:
        return self.is_won or len(self.guesses) >= self.max_attempts

    @staticmethod
    def _all_green(guess: Guess) -> bool:
        return all(f is Feedback.GREEN for f in guess.feedback)

    @staticmethod
    def score(guess: str, secret: str) -> List[Feedback]:
        """Compute Wordle-style feedback for a guess against a secret.

        The matching is done greedily: greens first, then yellows while
        respecting the number of remaining instances of each letter.
        """
        guess = guess.lower()
        secret = secret.lower()
        result = [Feedback.GRAY] * len(guess)

        remaining: dict = {}
        for ch in secret:
            remaining[ch] = remaining.get(ch, 0) + 1

        # Pass 1: mark exact matches.
        for i, ch in enumerate(guess):
            if i < len(secret) and secret[i] == ch:
                result[i] = Feedback.GREEN
                remaining[ch] -= 1

        # Pass 2: mark misplaced letters that are still available.
        for i, ch in enumerate(guess):
            if result[i] is Feedback.GREEN:
                continue
            if remaining.get(ch, 0) > 0:
                result[i] = Feedback.YELLOW
                remaining[ch] -= 1

        return result

    def submit(self, word: str) -> List[Feedback]:
        """Submit a guess, recording feedback. Raises ValueError for invalid input."""
        if self.is_over:
            raise ValueError("Game is already over.")
        if not word or not word.isalpha():
            raise ValueError("Guesses must contain only letters.")
        if len(word) != len(self.secret):
            raise ValueError(
                f"Guess must be {len(self.secret)} letters long."
            )
        feedback = self.score(word, self.secret)
        self.guesses.append(Guess(word=word.lower(), feedback=feedback))
        return feedback

    def play(self, input_fn: Callable[[str], str], output_fn=lambda m: None,
             colors: bool = True) -> bool:
        """Interactive loop. Returns True if the player won."""
        output_fn(f"Guess the {len(self.secret)}-letter word! You have "
                 f"{self.max_attempts} attempts.")
        while not self.is_over:
            guess = input_fn(f"Attempt {len(self.guesses) + 1}/{self.max_attempts}: ").strip()
            try:
                feedback = self.submit(guess)
            except ValueError as exc:
                output_fn(str(exc))
                continue
            output_fn(render(self.guesses[-1], colors=colors))
        if self.is_won:
            output_fn(f"Won in {len(self.guesses)} attempt(s)! The word was "
                      f"'{self.secret}'.")
        else:
            output_fn(
                f"Out of attempts. The word was '{self.secret}'."
            )
        return self.is_won


def render(guess: Guess, colors: bool = True) -> str:
    """Render a single guess row with optional ANSI colors."""
    symbols = {
        Feedback.GREEN: "g",
        Feedback.YELLOW: "y",
        Feedback.GRAY: "x",
    }
    plain = " ".join(
        f"{symbols[f]}{ch}{symbols[f]}" for ch, f in zip(guess.word, guess.feedback)
    )
    if not colors:
        return plain
    codes = {
        Feedback.GREEN: "\033[42;97m",
        Feedback.YELLOW: "\033[43;97m",
        Feedback.GRAY: "\033[47;30m",
    }
    reset = "\033[0m"
    cells = []
    for ch, f in zip(guess.word, guess.feedback):
        cells.append(f"{codes[f]} {ch} {reset}")
    return "".join(cells)
