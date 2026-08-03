"""Core Markov chain model: training and generation.

A word-level n-gram Markov model. During training we record, for every
sequence of `order` words, the multiset of words that follow it. During
generation we walk the chain, picking the next word from the observed
distribution (weighted or uniformly).

Design notes:
  * State keys are tuples of words, so any reasonable order is cheap.
  * A weight of ``None`` means "pick uniformly from the seen continuations";
    an integer or float enables frequency-weighted sampling.
"""

from __future__ import annotations

import random
from collections import defaultdict
from collections.abc import Iterable, Iterator
from pathlib import Path
from typing import Optional

# Sentinel used to mark the end of a document so a chain can terminate.
END = "\x00"
# Splits on any run of whitespace; keeps punctuation attached to words.
_TOKENIZE = str.split


class MarkovModel:
    """An order-``n`` word-level Markov chain."""

    def __init__(self, order: int = 2, weighted: bool = True) -> None:
        if order < 1:
            raise ValueError("order must be >= 1")
        self.order = order
        self.weighted = weighted
        self._follows: defaultdict[
            tuple[str, ...], defaultdict[Optional[str], int]
        ] = defaultdict(lambda: defaultdict(int))
        self._distinct = 0

    # -- training ---------------------------------------------------------

    def train(self, text: str) -> "MarkovModel":
        """Feed one document (a string) into the model."""
        start_state = (END,) * self.order
        state = start_state
        for token in _TOKENIZE(text):
            self._follows[state][token] += 1
            # Shift: keep the last (order - 1) tokens plus the new one.
            state = state[1:] + (token,)
        self._follows[state][END] += 1
        self._distinct += 1
        return self

    def train_iter(self, docs: Iterable[str]) -> "MarkovModel":
        """Train on any iterable of documents."""
        for doc in docs:
            self.train(doc)
        return self

    # -- introspection ----------------------------------------------------

    @property
    def vocabulary(self) -> int:
        """Number of distinct word tokens seen (excludes the END sentinel)."""
        words = {
            w
            for row in self._follows.values()
            for w in row
            if w != END
        }
        return len(words)

    @property
    def documents(self) -> int:
        return self._distinct

    # -- generation -------------------------------------------------------

    def generate(
        self,
        *,
        max_words: int = 50,
        seed: Optional[str] = None,
        rng: Optional[random.Random] = None,
    ) -> str:
        """Generate a new sequence of up to ``max_words`` words.

        Starts from a fresh document boundary, so output is not seeded from
        any particular text.
        """
        if not self._follows:
            raise ValueError("model has not been trained")
        rnd = rng if rng is not None else random.Random(seed)
        state = (END,) * self.order
        out: list[str] = []
        for _ in range(max_words):
            next_word = self._pick(state, rnd)
            if next_word is END:
                break
            out.append(next_word)
            state = state[1:] + (next_word,)
        return " ".join(out)

    def _pick(self, state: tuple[str, ...], rnd: random.Random) -> Optional[str]:
        options = self._follows.get(state)
        if not options:
            return END
        if self.weighted:
            choices = list(options)
            weights = [options[c] for c in choices]
            return rnd.choices(choices, weights=weights)[0]
        return rnd.choice(list(options))

    def __bool__(self) -> bool:
        return bool(self._follows)

    def __len__(self) -> int:
        return self._distinct


def _tokenize_docs(text: str) -> Iterator[str]:
    """Split a blob of text into documents on blank lines."""
    doc = []
    for line in text.splitlines():
        if line.strip():
            doc.append(line)
        elif doc:
            yield " ".join(doc)
            doc = []
    if doc:
        yield " ".join(doc)


def train_on_text(model: MarkovModel, text: str) -> MarkovModel:
    """Train ``model`` on arbitrary text, splitting on blank lines."""
    return model.train_iter(_tokenize_docs(text))


def train_on_file(model: MarkovModel, path: str | Path) -> MarkovModel:
    """Train ``model`` on the contents of a file (blank-line separated)."""
    return train_on_text(model, Path(path).read_text(encoding="utf-8"))
