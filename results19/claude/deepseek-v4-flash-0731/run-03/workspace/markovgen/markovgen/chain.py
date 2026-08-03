"""A greedy, order-N Markov chain text generator.

The chain is learned from example text: for each context of N previous
tokens, we record every token that has followed it. To generate, we start
from a seed context and repeatedly pick the next token that has been seen
most often after the current context (ties broken by weighted random
choice, so the output is not fully deterministic).

Token probabilities are stored as integer counts. On tie, we sample among
the tied candidates proportional to their counts.
"""

from __future__ import annotations

import random
from collections import Counter, defaultdict
from typing import Iterable, Sequence

from .text import tokenize


class MarkovChain:
    """Order-N Markov chain over whitespace-delimited tokens.

    Parameters
    ----------
    order : int
        Number of preceding tokens used as the context. Must be >= 1.
    rng : random.Random, optional
        Source of randomness for tie-breaking. Injected for determinism
        in tests; defaults to a fresh global Random.
    """

    def __init__(self, order: int = 2, rng: random.Random | None = None) -> None:
        if order < 1:
            raise ValueError("order must be >= 1")
        self.order = order
        self._rng = rng or random.Random()
        # context (tuple of tokens) -> Counter of following tokens.
        self._transitions: dict[tuple[str, ...], Counter[str]] = defaultdict(Counter)
        self._starts: list[tuple[str, ...]] = []
        self._token_count = 0

    def fit(self, texts: str | Iterable[str]) -> "MarkovChain":
        """Learn transition probabilities from one text or many documents."""
        if isinstance(texts, str):
            texts = [texts]
        for text in texts:
            self._learn_text(text)
        return self

    def _learn_text(self, text: str) -> None:
        tokens = tokenize(text)
        if not tokens:
            return
        self._token_count += len(tokens)
        n = self.order
        # Every sliding window of n tokens is a potential start context.
        for i in range(len(tokens) - n + 1):
            self._starts.append(tuple(tokens[i : i + n]))
        # Record each context -> following token transition.
        for i in range(len(tokens) - n):
            ctx = tuple(tokens[i : i + n])
            nxt = tokens[i + n]
            self._transitions[ctx][nxt] += 1

    def generate(self, length: int, seed: Sequence[str] | None = None) -> str:
        """Generate a string of up to ``length`` tokens.

        ``seed`` optionally fixes the starting context (must be a sequence
        of exactly ``order`` tokens for an exact match; shorter seeds are
        matched by suffix).
        """
        if length < 1:
            return ""

        ctx = self._choose_start(seed)
        if ctx is None:
            return ""

        out: list[str] = list(ctx)
        while len(out) < length:
            counts = self._transitions.get(ctx)
            if not counts:
                break
            nxt = self._pick(counts)
            out.append(nxt)
            ctx = tuple(out[-self.order :])
        return " ".join(out[:length])

    def _choose_start(self, seed: Sequence[str] | None) -> tuple[str, ...] | None:
        if seed is not None:
            seed = tuple(seed)
            # Prefer an exact-order match, then shrink from the front so the
            # tail of the seed still anchors the generation.
            for size in range(min(len(seed), self.order), 0, -1):
                candidates = [s for s in self._starts if s[-size:] == seed[-size:]]
                if candidates:
                    return self._rng.choice(candidates)
            return None
        if not self._starts:
            return None
        return self._rng.choice(self._starts)

    def _pick(self, counts: Counter[str]) -> str:
        """Return the most-common token, tie-breaking by weighted choice."""
        max_count = max(counts.values())
        tied = Counter({tok: c for tok, c in counts.items() if c == max_count})
        return self._weighted_choice(tied)

    def _weighted_choice(self, counts: Counter[str]) -> str:
        total = sum(counts.values())
        roll = self._rng.random() * total
        upto = 0.0
        for tok, c in counts.items():
            upto += c
            if roll <= upto:
                return tok
        return next(iter(counts))  # unreachable; safety net

    @property
    def token_count(self) -> int:
        """Total number of tokens seen during fitting."""
        return self._token_count

    @property
    def start_count(self) -> int:
        """Number of distinct start contexts."""
        return len(self._starts)

    @property
    def transition_count(self) -> int:
        """Number of (context, next-token) pairs recorded."""
        return sum(len(c) for c in self._transitions.values())
