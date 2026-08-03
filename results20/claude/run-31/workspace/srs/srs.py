"""A tiny spaced-repetition (SM-2) flashcard CLI with zero dependencies.

Usage:
    python3 srs.py add "q" "a" [deck]
    python3 srs.py review [deck]
    python3 srs.py stats [deck]
    python3 srs.py newdeck "name"
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional

# ---------------------------------------------------------------------------
# SM-2 scheduling
# ---------------------------------------------------------------------------

# Minimum interval in days; 1st review -> 1, 2nd -> 6, then *ease each time.
MIN_INTERVAL = 1.0
HARD_FACTOR = 1.2  # extra multiplier applied when you answer "hard"
EASE_MIN = 1.3
EASE_MAX = 2.5


def next_interval(step: int, ease: float, quality: int, last_interval: float) -> float:
    """Return the days until the next review, per SM-2.

    quality is a grade 0..5 (from the CLI: 3=hard, 4=good, 5=easy).
    step is how many times the card has been reviewed (0 before the first).
    """
    if quality < 3:
        # Failed: reset to day 1 and let the interval rebuild naturally.
        return MIN_INTERVAL
    if step == 0:
        return MIN_INTERVAL
    if step == 1:
        return 6.0
    interval = last_interval * ease * HARD_FACTOR if quality == 3 else last_interval * ease
    return round(max(MIN_INTERVAL, interval), 1)


def updated_ease(quality: int, ease: float) -> float:
    """SM-2 ease factor update. quality < 3 (failure) drops ease; <4 softens it."""
    if quality < 3:
        ease -= 0.2
    elif quality == 3:
        ease -= 0.15
    elif quality == 5:
        ease += 0.15
    return min(EASE_MAX, max(EASE_MIN, round(ease, 2)))


# ---------------------------------------------------------------------------
# Data model + persistence
# ---------------------------------------------------------------------------

@dataclass
class Card:
    front: str
    back: str
    deck: str = "default"
    step: int = 0            # number of successful reviews so far
    ease: float = 2.5
    interval: float = 0.0    # current interval in days (0 = never reviewed)
    due: float = 0.0         # unix timestamp when it becomes due (0 = due now)
    reps: int = 0
    lapses: int = 0
    history: List[int] = field(default_factory=list)  # last quality grades

    def to_dict(self) -> dict:
        return {
            "front": self.front, "back": self.back, "deck": self.deck,
            "step": self.step, "ease": self.ease, "interval": self.interval,
            "due": self.due, "reps": self.reps, "lapses": self.lapses,
            "history": self.history,
        }

    @classmethod
    def from_dict(cls, d: dict) -> "Card":
        return cls(
            front=d["front"], back=d["back"], deck=d.get("deck", "default"),
            step=d.get("step", 0), ease=d.get("ease", 2.5),
            interval=d.get("interval", 0.0), due=d.get("due", 0.0),
            reps=d.get("reps", 0), lapses=d.get("lapses", 0),
            history=d.get("history", []),
        )


class Store:
    """JSON-file-backed collection of cards + deck registry.

    Data is a dict: {"decks": [<name>, ...], "cards": [<card dict>, ...]}.
    """

    def __init__(self, path: Path):
        self.path = path
        self.cards: Dict[str, Card] = {}   # (deck, front) -> Card
        self.deck_names: set = set()
        self._load()

    def _load(self) -> None:
        if not self.path.exists():
            return
        try:
            data = json.loads(self.path.read_text())
        except (ValueError, OSError):
            print(f"warning: could not read {self.path}; starting empty", file=sys.stderr)
            return
        self.deck_names = set(data.get("decks", []))
        for d in data.get("cards", []):
            card = Card.from_dict(d)
            self.cards[(card.deck, card.front)] = card
            self.deck_names.add(card.deck)

    def save(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        blob = {
            "decks": sorted(self.deck_names),
            "cards": [c.to_dict() for c in sorted(self.cards.values(), key=lambda c: c.front)],
        }
        tmp = self.path.with_suffix(".tmp")
        tmp.write_text(json.dumps(blob, indent=2))
        tmp.replace(self.path)  # atomic-ish write

    def get(self, deck: str, front: str) -> Optional[Card]:
        return self.cards.get((deck, front))

    def add(self, card: Card) -> None:
        self.cards[(card.deck, card.front)] = card
        self.deck_names.add(card.deck)

    def cards_for(self, deck: Optional[str]) -> List[Card]:
        out = [c for (d, _), c in self.cards.items() if deck is None or d == deck]
        return sorted(out, key=lambda c: (c.deck, c.due))

    def decks(self) -> List[str]:
        return sorted(self.deck_names)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def _prompt_int(prompt: str, lo: int, hi: int) -> int:
    while True:
        raw = input(prompt).strip()
        if raw == "" and lo == 0:  # empty = grade 0 (fail) is not allowed here
            continue
        try:
            v = int(raw)
        except ValueError:
            print(f"  enter a number between {lo} and {hi}")
            continue
        if lo <= v <= hi:
            return v
        print(f"  enter a number between {lo} and {hi}")


def cmd_newdeck(store: Store, deck: str) -> int:
    if deck in store.decks():
        print(f"deck '{deck}' already exists")
        return 1
    store.deck_names.add(deck)
    store.save()
    print(f"created deck '{deck}'")
    return 0


def cmd_add(store: Store, front: str, back: str, deck: str) -> int:
    if store.get(deck, front) is not None:
        print(f"card already exists in '{deck}': {front!r}")
        return 1
    store.add(Card(front=front, back=back, deck=deck))
    store.save()
    print(f"added to '{deck}' (due now): {front}")
    return 0


def cmd_review(store: Store, deck: Optional[str]) -> int:
    now = time.time()
    due = [c for c in store.cards_for(deck) if c.due <= now]
    if not due:
        print("nothing due right now 🎉")
        return 0

    reviewed = 0
    for card in due:
        print("\n" + "=" * 60)
        print(card.front)
        input("  [press Enter to reveal] ")
        print("-" * 60)
        print(card.back)
        print("-" * 60)
        grade = _prompt_int("  grade? (0-2 fail, 3 hard, 4 good, 5 easy) [4]: ", 0, 5)
        if grade == "":
            grade = 4

        failed = grade < 3
        card.interval = next_interval(card.step, card.ease, grade, card.interval)
        card.ease = updated_ease(grade, card.ease)
        card.step = 0 if failed else card.step + 1
        card.reps += 1
        card.lapses += 1 if failed else 0
        card.history.append(grade)
        card.due = now + card.interval * 86400 if not failed else now + MIN_INTERVAL * 86400
        reviewed += 1
        print(f"  -> next in {card.interval:.1f} days (ease {card.ease:.2f})")
        store.save()  # persist after every card so progress survives interruption

    print(f"\nreviewed {reviewed} card(s)")
    return 0


def cmd_stats(store: Store, deck: Optional[str]) -> int:
    cards = store.cards_for(deck)
    now = time.time()
    if not cards:
        print("no cards" + (f" in '{deck}'" if deck else ""))
        return 1
    due = [c for c in cards if c.due <= now]
    new = [c for c in cards if c.reps == 0]
    mature = [c for c in cards if c.interval >= 21]
    lapses = sum(c.lapses for c in cards)
    reps = sum(c.reps for c in cards)
    avg_ease = sum(c.ease for c in cards) / len(cards)
    print(f"deck(s): {', '.join(sorted({c.deck for c in cards}))}")
    print(f"cards:   {len(cards)}  (due now: {len(due)}, new: {len(new)}, mature: {len(mature)})")
    print(f"reps:    {reps}  lapses: {lapses}")
    print(f"avg ease:{avg_ease:.2f}  (interval range: {min(c.interval for c in cards):.1f}-{max(c.interval for c in cards):.1f} d)")
    return 0


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(prog="srs", description="spaced-repetition flashcards")
    sub = parser.add_subparsers(dest="cmd", required=True)

    p_new = sub.add_parser("newdeck", help="create a deck")
    p_new.add_argument("deck")

    p_add = sub.add_parser("add", help="add a card")
    p_add.add_argument("front")
    p_add.add_argument("back")
    p_add.add_argument("deck", nargs="?", default="default")

    p_rev = sub.add_parser("review", help="review due cards")
    p_rev.add_argument("deck", nargs="?")

    p_st = sub.add_parser("stats", help="show deck statistics")
    p_st.add_argument("deck", nargs="?")

    p = parser.parse_args(argv)
    store = Store(Path(os.environ.get("SRS_FILE", "cards.json")))

    if p.cmd == "newdeck":
        return cmd_newdeck(store, p.deck)
    if p.cmd == "add":
        return cmd_add(store, p.front, p.back, p.deck)
    if p.cmd == "review":
        return cmd_review(store, p.deck)
    if p.cmd == "stats":
        return cmd_stats(store, p.deck)
    return 1


if __name__ == "__main__":
    try:
        sys.exit(main())
    except (EOFError, KeyboardInterrupt):
        print("\n(interrupted; progress is saved)", file=sys.stderr)
        sys.exit(130)
