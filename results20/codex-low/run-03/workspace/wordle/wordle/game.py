"""Core game logic with standard-library-only implementation."""

import random
from typing import List, Optional, Tuple

from .words import ANSWERS, random_word

MAX_GUESSES = 6
GREEN = "G"
YELLOW = "Y"
GRAY = "X"


class Wordle:
    """Holds a single game's state and resolves guess feedback."""

    def __init__(self, answer: Optional[str] = None):
        if answer is None:
            answer = random_word()
        answer = answer.upper()
        if len(answer) != 5 or not answer.isalpha():
            raise ValueError("Answer must be a 5-letter word")
        self.answer = answer
        self.guesses: List[str] = []
        self.patterns: List[List[str]] = []
        self._solved = False

    @property
    def finished(self) -> bool:
        return self._solved or len(self.guesses) >= MAX_GUESSES

    @property
    def won(self) -> bool:
        return self._solved

    def validate(self, guess: str) -> Optional[str]:
        """Return an error message, or None if the guess is acceptable."""
        guess = guess.upper()
        if len(guess) != 5:
            return "Word must be exactly 5 letters."
        if not guess.isalpha():
            return "Word must contain only letters."
        return None

    def guess(self, word: str) -> Tuple[str, List[str]]:
        """Submit a guess; returns (normalized guess, pattern list)."""
        word = word.upper()
        err = self.validate(word)
        if err:
            raise ValueError(err)
        self.guesses.append(word)
        if word == self.answer:
            pattern = [GREEN] * 5
            self.patterns.append(pattern)
            self._solved = True
            return word, pattern

        remaining: List[str] = []
        pattern = [GRAY] * 5
        for i, letter in enumerate(word):
            if letter == self.answer[i]:
                pattern[i] = GREEN
            else:
                remaining.append(self.answer[i])

        for i, letter in enumerate(word):
            if pattern[i] == GRAY and letter in remaining:
                pattern[i] = YELLOW
                remaining.remove(letter)

        self.patterns.append(pattern)
        return word, pattern
