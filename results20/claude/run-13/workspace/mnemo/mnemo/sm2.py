"""SM-2 spaced-repetition scheduling algorithm.

Implements the classic SuperMemo SM-2 algorithm used by Anki and most
flashcard apps. The scheduler is a pure function operating on a card's
current state, so it is easy to unit test and reason about.

Card state fields:
    ease      - multiplier controlling how interval grows (default 2.5)
    interval  - current review interval in days (0 for a brand-new card)
    reps      - number of successful reviews so far
    lapses    - number of times the card was forgotten
"""

from __future__ import annotations

from dataclasses import dataclass

# Quality of response, per the SM-2 rubric:
QUALITY_BLACKOUT = 0      # total blackout
QUALITY_WRONG = 1         # wrong response; hard to recall
QUALITY_WRONG_EASY = 2    # wrong response; easy to recall
QUALITY_HARD = 3          # correct but difficult
QUALITY_GOOD = 4          # correct after hesitation
QUALITY_EASY = 5          # perfect response

MIN_EASE = 1.3
DEFAULT_EASE = 2.5

# An "easy" review always jumps the interval by 1 day regardless of stage;
# a "hard" review truncates the interval growth.
HARD_IVL_FACTOR = 1.2
EASY_IVL_FACTOR = 1.3

_DATACLASS = dataclass(frozen=True)


@_DATACLASS
class CardState:
    """Immutable scheduling state for a card."""

    ease: float = DEFAULT_EASE
    interval: int = 0
    reps: int = 0
    lapses: int = 0


def _next_interval(state: CardState, quality: int) -> int:
    """Interval growth rules (SM-2), independent of the pass/fail split."""
    ivl = state.interval
    if ivl < 1:
        return 1
    if ivl == 1:
        return 6
    # For cards past the 6-day mark, grow by the ease factor; clamp the
    # applied factor so later reviews do not accelerate without bound.
    return round(ivl * max(state.ease, HARD_IVL_FACTOR))


def schedule(state: CardState, quality: int, now_days: int) -> CardState:
    """Return the new card state after a review rated ``quality`` on day
    ``now_days`` (an integer day number, e.g. ``days_since_epoch``).

    Quality 0-2 is a failed review (the card is "lapsed": interval resets
    to 1 day, ease drops); quality 3 or higher is a successful review.
    """
    if quality < 0 or quality > 5:
        raise ValueError(f"quality must be 0..5, got {quality}")

    if quality < 3:
        # Lapse: reschedule for tomorrow, reduce ease, count a lapse.
        return CardState(
            ease=max(state.ease - 0.2, MIN_EASE),
            interval=1,
            reps=0,
            lapses=state.lapses + 1,
        )

    # Successful review: grow the interval.
    interval = _next_interval(state, quality)
    if quality == QUALITY_EASY:
        interval *= EASY_IVL_FACTOR
    elif quality == QUALITY_HARD:
        interval = max(1, round(interval / HARD_IVL_FACTOR))

    # Only a hard pass (3) shaves ease; good/easy keep it stable.
    ease = state.ease if quality >= QUALITY_GOOD else max(state.ease - 0.15, MIN_EASE)

    return CardState(
        ease=ease,
        interval=interval,
        reps=state.reps + 1,
        lapses=state.lapses,
    )
