"""Core password and passphrase generation logic."""

from __future__ import annotations

import math
import secrets
import string
from dataclasses import dataclass, replace
from typing import Callable, Iterable

LOWERCASE = string.ascii_lowercase
UPPERCASE = string.ascii_uppercase
DIGITS = string.digits
SYMBOLS = "!@#$%^&*()-_=+[]{};:,.<>?"

# Characters commonly confused with one another (1 vs l, 0 vs O, etc.).
AMBIGUOUS = "Il1O0"

DEFAULT_WORDLIST = (
    "apple bath calm dawn echo fern gleam hatch ivory jade koi lime mist nova "
    "oak pine quill rose shore tide urn vine wren yew ember frost gale haze "
    "iris jolt kale ledge moat nook oasis pearl quay reef sage thyme unit "
    "veil wisp yawn zeal amber bay cape dune fern gull hill isle knoll loom "
    "meadow nook orbit plume quill ridge slope trail upland vale woven "
).split()


@dataclass(frozen=True)
class PasswordConfig:
    """Settings controlling password generation."""

    length: int = 16
    lowercase: bool = True
    uppercase: bool = True
    digits: bool = True
    symbols: bool = True
    exclude_ambiguous: bool = False
    rng: Callable[[int], int] | None = None


def _secure_rng(upper_bound: int) -> int:
    return secrets.randbelow(upper_bound)


def _char_pools(config: PasswordConfig) -> list[str]:
    sets = []
    if config.lowercase:
        sets.append(LOWERCASE)
    if config.uppercase:
        sets.append(UPPERCASE)
    if config.digits:
        sets.append(DIGITS)
    if config.symbols:
        sets.append(SYMBOLS)
    if not sets:
        sets.append(LOWERCASE)
    if config.exclude_ambiguous:
        sets = ["".join(c for c in pool if c not in AMBIGUOUS) for pool in sets]
    return sets


def generate_password(config: PasswordConfig | None = None) -> str:
    """Generate a random password matching the requested character sets.

    Every enabled pool is guaranteed at least one character; remaining slots
    are filled randomly, then the result is shuffled to remove pool bias.
    """
    cfg = config or PasswordConfig()
    if cfg.length < 1:
        raise ValueError("length must be at least 1")

    pools = _char_pools(cfg)
    rng = cfg.rng or _secure_rng

    slots = [pool[rng(len(pool))] for pool in pools]
    while len(slots) < cfg.length:
        pool = pools[rng(len(pools))]
        slots.append(pool[rng(len(pool))])

    # Shuffle the guaranteed + filler characters together.
    for i in range(len(slots) - 1, 0, -1):
        j = rng(i + 1)
        slots[i], slots[j] = slots[j], slots[i]
    return "".join(slots)


def generate_passphrase(
    words: int = 6,
    separator: str = "-",
    capitalize: bool = False,
    wordlist: Iterable[str] | None = None,
    rng: Callable[[int], int] | None = None,
) -> str:
    """Generate a Diceware-style passphrase from a wordlist."""
    if words < 1:
        raise ValueError("words must be at least 1")

    pool = list(wordlist) if wordlist is not None else _read_words()
    if len(pool) < 2:
        raise ValueError("wordlist must contain at least 2 words")

    rng = rng or _secure_rng
    selected = []
    for _ in range(words):
        word = pool[rng(len(pool))]
        selected.append(word.capitalize() if capitalize else word)
    return separator.join(selected)


def entropy(pool_size: int, length: int) -> float:
    """Return the Shannon entropy in bits for a password of a given pool/length."""
    if pool_size < 1:
        raise ValueError("pool_size must be at least 1")
    if length < 0:
        raise ValueError("length must be non-negative")
    if length == 0:
        return 0.0
    return length * math.log2(pool_size)


def pool_size(config: PasswordConfig) -> int:
    """Compute the total distinct character pool size for a config."""
    return sum(len(pool) for pool in _char_pools(config))


def generate_token(
    length: int = 32,
    alphabet: str = LOWERCASE + UPPERCASE + DIGITS,
    rng: Callable[[int], int] | None = None,
) -> str:
    """Generate a high-entropy token (e.g. API keys) from an alphabet."""
    if length < 1:
        raise ValueError("length must be at least 1")
    if not alphabet:
        raise ValueError("alphabet must be non-empty")
    rng = rng or _secure_rng
    return "".join(alphabet[rng(len(alphabet))] for _ in range(length))


def _read_words() -> list[str]:
    """Read a dictionary file into a wordlist, falling back to the default."""
    try:
        with open("/usr/share/dict/words", "r", encoding="utf-8") as handle:
            words = [
                w
                for w in (line.strip().lower() for line in handle)
                if w.isalpha() and 3 <= len(w) <= 9
            ]
        if len(words) >= 100:
            return words
    except OSError:
        pass
    return list(DEFAULT_WORDLIST)
