"""Core passphrase generation logic with cryptographic randomness."""
from __future__ import annotations

import secrets
from dataclasses import dataclass


@dataclass(frozen=True)
class Passphrase:
    words: tuple[str, ...]
    separator: str
    entropy_bits: float

    def as_str(self) -> str:
        return self.separator.join(self.words)


def available_words() -> list[str]:
    from passgen import words as words_pkg

    return list(words_pkg.WORD_LIST)


def sample_indices(count: int, pool_size: int) -> list[int]:
    """Return `count` unique indices drawn uniformly from [0, pool_size)."""
    if count < 1:
        raise ValueError("count must be >= 1")
    if pool_size < count:
        raise ValueError("pool too small for requested count")
    # secrets.randbelow is backed by the best available entropy source.
    seen: set[int] = set()
    result: list[int] = []
    while len(result) < count:
        idx = secrets.randbelow(pool_size)
        if idx in seen:
            continue
        seen.add(idx)
        result.append(idx)
    return result


def generate(
    count: int = 6,
    pool: list[str] | None = None,
    separator: str = "-",
) -> Passphrase:
    """Generate a passphrase of `count` unique words from `pool`."""
    word_pool = pool if pool is not None else available_words()
    if count < 1:
        raise ValueError("count must be >= 1")
    if len(word_pool) < count:
        raise ValueError(
            f"pool has only {len(word_pool)} words, need at least {count}"
        )

    indices = sample_indices(count, len(word_pool))
    chosen = tuple(word_pool[i] for i in indices)

    per_word_bits = len(word_pool).bit_length() - 1
    entropy_bits = per_word_bits * count

    return Passphrase(words=chosen, separator=separator, entropy_bits=entropy_bits)
