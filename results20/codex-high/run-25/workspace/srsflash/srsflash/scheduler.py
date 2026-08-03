"""Spaced-repetition scheduling based on the SM-2 algorithm."""

from __future__ import annotations

import datetime as dt
import json


class Card:
    """A single flashcard with its scheduling state."""

    def __init__(
        self,
        front: str,
        back: str,
        *,
        ease: float = 2.5,
        interval_days: int = 0,
        repetitions: int = 0,
        due: dt.datetime | None = None,
    ) -> None:
        self.front = front
        self.back = back
        self.ease = ease
        self.interval_days = interval_days
        self.repetitions = repetitions
        self.due = due or dt.datetime.now(dt.timezone.utc)

    def is_due(self, now: dt.datetime | None = None) -> bool:
        now = now or dt.datetime.now(dt.timezone.utc)
        return self.due <= now

    def review(self, quality: int, now: dt.datetime | None = None) -> "Card":
        """Update scheduling state given a quality grade (0-5)."""
        if not 0 <= quality <= 5:
            raise ValueError("quality must be between 0 and 5")
        now = now or dt.datetime.now(dt.timezone.utc)

        if quality < 3:
            self.repetitions = 0
            self.interval_days = 1
        else:
            self.repetitions += 1
            if self.repetitions == 1:
                self.interval_days = 1
            elif self.repetitions == 2:
                self.interval_days = 6
            else:
                self.interval_days = round(self.interval_days * self.ease)
            self.ease = max(1.3, self.ease + (0.1 - (5 - quality) * (0.08 + (5 - quality) * 0.02)))

        self.due = now + dt.timedelta(days=self.interval_days)
        return self

    def to_dict(self) -> dict:
        return {
            "front": self.front,
            "back": self.back,
            "ease": self.ease,
            "interval_days": self.interval_days,
            "repetitions": self.repetitions,
            "due": self.due.isoformat(),
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Card":
        return cls(
            front=data["front"],
            back=data["back"],
            ease=data.get("ease", 2.5),
            interval_days=data.get("interval_days", 0),
            repetitions=data.get("repetitions", 0),
            due=dt.datetime.fromisoformat(data["due"]),
        )


class Deck:
    """A collection of cards persisted as JSON."""

    def __init__(self, path: str) -> None:
        self.path = path
        self.cards: list[Card] = []
        self.load()

    def load(self) -> None:
        try:
            with open(self.path, encoding="utf-8") as fh:
                data = json.load(fh)
        except FileNotFoundError:
            self.cards = []
            return
        self.cards = [Card.from_dict(item) for item in data.get("cards", [])]

    def save(self) -> None:
        data = {"cards": [card.to_dict() for card in self.cards]}
        with open(self.path, "w", encoding="utf-8") as fh:
            json.dump(data, fh, indent=2)

    def add(self, front: str, back: str) -> Card:
        card = Card(front, back)
        self.cards.append(card)
        return card

    def remove(self, index: int) -> Card:
        return self.cards.pop(index)

    def due_cards(self, now: dt.datetime | None = None) -> list[Card]:
        return [c for c in self.cards if c.is_due(now)]
