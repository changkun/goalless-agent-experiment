"""Curiosity prompts and micro-adventures."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum, auto
from pathlib import Path
import json
import random


class Category(Enum):
    """Prompt category."""

    OBSERVE = auto()
    CREATE = auto()
    CONNECT = auto()
    MOVE = auto()
    WONDER = auto()

    def __str__(self) -> str:
        return self.name.title()


@dataclass(frozen=True, slots=True)
class Prompt:
    """A single curiosity prompt."""

    category: Category
    text: str
    why: str


DEFAULT_PROMPTS: tuple[Prompt, ...] = (
    Prompt(
        Category.OBSERVE,
        "Find a color you never noticed on your usual route.",
        "Attention is learnable; novelty hides in plain sight.",
    ),
    Prompt(
        Category.CREATE,
        "Make something edible with exactly three ingredients.",
        "Constraints unlock creativity better than abundance.",
    ),
    Prompt(
        Category.CONNECT,
        "Ask someone what they loved doing at age ten.",
        "Shared memories build trust faster than small talk.",
    ),
    Prompt(
        Category.MOVE,
        "Take a five-minute walk with no destination.",
        "Motion changes emotion; the mind rides the body.",
    ),
    Prompt(
        Category.WONDER,
        "Write down one question you genuinely cannot answer.",
        "Unanswered questions keep the mind alive.",
    ),
    Prompt(
        Category.OBSERVE,
        "Listen to a familiar song and focus only on the bass line.",
        "Rediscovery beats discovery when attention is fresh.",
    ),
    Prompt(
        Category.CREATE,
        "Describe your current mood in exactly six words.",
        "Brevity forces honesty.",
    ),
    Prompt(
        Category.CONNECT,
        "Send a message appreciating a small thing someone did.",
        "Gratitude compounds when expressed.",
    ),
    Prompt(
        Category.MOVE,
        "Stand up and stretch toward the ceiling for thirty seconds.",
        "Small physical resets prevent mental stagnation.",
    ),
    Prompt(
        Category.WONDER,
        "Invent a word for a feeling you had today.",
        "Naming an experience makes it shareable.",
    ),
)


def load_prompts(path: Path | None = None) -> tuple[Prompt, ...]:
    """Load prompts from a JSON file, falling back to defaults."""
    if path is None:
        return DEFAULT_PROMPTS

    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return DEFAULT_PROMPTS

    try:
        return tuple(
            Prompt(
                category=Category[entry["category"].upper()],
                text=entry["text"],
                why=entry["why"],
            )
            for entry in raw
        )
    except (KeyError, TypeError, ValueError):
        return DEFAULT_PROMPTS


def pick(prompts: tuple[Prompt, ...], category: Category | None = None) -> Prompt | None:
    """Return a random prompt, optionally filtered by category."""
    pool = prompts if category is None else tuple(p for p in prompts if p.category == category)
    if not pool:
        return None
    return random.choice(pool)
