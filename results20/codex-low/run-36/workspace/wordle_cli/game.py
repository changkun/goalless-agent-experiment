"""Core logic for a Wordle-style word guessing game."""

from dataclasses import dataclass
from enum import Enum
from typing import List


class Feedback(str, Enum):
    """Per-letter feedback colors in a guess."""

    CORRECT = "G"   # letter is in the right position (green)
    PRESENT = "Y"   # letter is in the word but wrong position (yellow)
    ABSENT = "B"    # letter is not in the word (black/gray)


@dataclass(frozen=True)
class Wordle:
    """Configuration for a single game."""

    answer: str
    max_guesses: int = 6

    @classmethod
    def from_word(
        cls, answer: str, max_guesses: int = 6
    ) -> "Wordle":
        word = answer.strip().upper()
        if not word.isalpha() or len(word) != 5:
            raise ValueError("answer must be a 5-letter word")
        return cls(answer=word, max_guesses=max_guesses)


def score_guess(guess: str, answer: str) -> List[Feedback]:
    """Score a guess against the answer using Wordle rules.

    Handles duplicate letters correctly: a letter is marked CORRECT
    first, then PRESENT for remaining unmatched occurrences, and never
    over-reports a letter that does not appear in the answer.
    """
    guess = guess.upper()
    answer = answer.upper()

    if len(guess) != len(answer):
        raise ValueError("guess and answer must be the same length")

    result = [Feedback.ABSENT] * len(guess)
    counts = {}
    for ch in answer:
        counts[ch] = counts.get(ch, 0) + 1

    # Pass 1: mark exact matches.
    for i, (g, a) in enumerate(zip(guess, answer)):
        if g == a:
            result[i] = Feedback.CORRECT
            counts[g] -= 1

    # Pass 2: mark present-but-wrong-position letters.
    for i, g in enumerate(guess):
        if result[i] == Feedback.CORRECT:
            continue
        if counts.get(g, 0) > 0:
            result[i] = Feedback.PRESENT
            counts[g] -= 1

    return result


def is_correct(feedback: List[Feedback]) -> bool:
    """True when every letter of the guess was in the right place."""
    return all(f == Feedback.CORRECT for f in feedback)


def format_feedback(feedback: List[Feedback]) -> str:
    """Render feedback as a readable colored string for the terminal."""
    mapping = {
        Feedback.CORRECT: "\033[32m\u25cf\033[0m",   # green dot
        Feedback.PRESENT: "\033[33m\u25cf\033[0m",   # yellow dot
        Feedback.ABSENT: "\033[90m\u25cf\033[0m",    # gray dot
    }
    return " ".join(mapping[f] for f in feedback)
