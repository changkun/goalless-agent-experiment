"""Word lists for the game."""
import random

FIVE_LETTER_WORDS = [
    "crane", "slate", "crisp", "plumb", "around", "kebab", "pizza",
    "music", "horse", "stone", "light", "dream", "storm", "cloud",
    "river", "brain", "plant", "fruit", "north", "south", "eagle",
    "tiger", "apple", "grape", "lemon", "peach", "berry", "mango",
    "melon", "olive", "onion", "comic", "audio", "blaze", "charm",
    "dodge", "ember", "fable", "globe", "haste", "irony", "jolly",
    "koala", "lunar", "moist", "noble", "ozone",
]

ALL_WORDS = set(FIVE_LETTER_WORDS)


def random_word() -> str:
    """Return a random valid secret word."""
    return random.choice(FIVE_LETTER_WORDS)


def is_valid(word: str) -> bool:
    """Return True if word is an acceptable guess (all letters, correct length)."""
    return len(word) == 5 and word.isalpha()
