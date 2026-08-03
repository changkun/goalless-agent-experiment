#!/usr/bin/env python3
"""markov.py — a tiny, dependency-free Markov chain text generator.

Learns n-gram -> next-token transition counts from a corpus, then samples
new sequences. Higher `order` produces more coherent (but more derivative)
output; higher `temperature` produces more surprising output.

Usage:
    python3 markov.py --order 2 --count 200 --seed 42 < corpus.txt
    python3 markov.py (uses an embedded sample corpus if stdin is a tty)
"""

import argparse
import re
import random
import sys
from collections import Counter, defaultdict


SAMPLE_CORPUS = (
    "The sea is a relentless teacher. The sea swallows our mistakes and "
    "returns them polished as glass. Every wave arrives with a lesson, "
    "and every lesson is a wave. The moon pulls the tide, and the tide "
    "pulls the sailor home. Home is where the anchor finds the sand. "
    "The sand remembers every foot that walked here. We walk because we "
    "learn, and we learn because we walk. The horizon is not a wall; "
    "it is a door that never stops opening. Open your eyes to the water. "
    "The water keeps no grudges, only records. Records are the bones of "
    "memory, and memory is the tide that never rests. Rest, then rise. "
    "Rise with the sun, and the sun rises with you."
)


def tokenize(text: str) -> list[str]:
    """Split text into lowercase word tokens, preserving punctuation."""
    return re.findall(r"[\w']+|[.,;:!?]", text.lower())


def build_table(tokens: list[str], order: int) -> defaultdict[tuple, Counter]:
    """Map each n-gram prefix -> Counter of following tokens."""
    table = defaultdict(Counter)
    for i in range(len(tokens) - order):
        prefix = tuple(tokens[i : i + order])
        table[prefix][tokens[i + order]] += 1
    return table


def weighted_choice(counter: Counter, temperature: float) -> str:
    """Pick a token from a counter, flattening probabilities by temperature."""
    # temperature=0 => always the most common; temperature=1 => raw counts.
    items = list(counter.items())
    if temperature <= 0:
        return max(items, key=lambda kv: kv[1])[0]
    weights = [count ** (1.0 / temperature) for _, count in items]
    return random.choices([k for k, _ in items], weights=weights, k=1)[0]


def generate(
    table: defaultdict[tuple, Counter],
    order: int,
    count: int,
    temperature: float,
    rng_seed: int | None,
) -> str:
    random.seed(rng_seed)
    # Seed with the most common prefix in the table, then walk.
    start = max(table, key=lambda p: sum(table[p].values()))
    prefix = list(start)
    out = list(prefix)
    for _ in range(count):
        # Back off to a shorter suffix if the current prefix is a dead end
        # (a terminal n-gram with no recorded follower). Fall back to the
        # original start if every suffix is exhausted.
        key = None
        for n in range(order, 0, -1):
            cand = tuple(prefix[-n:])
            if table[cand]:
                key = cand
                break
        if key is None:
            prefix = list(start)
            key = tuple(prefix)
            out.append("…")
        nxt = weighted_choice(table[key], temperature)
        out.append(nxt)
        prefix = (prefix + [nxt])[-order:]
    return " ".join(out)


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.split(".")[0])
    ap.add_argument("--order", type=int, default=2, help="n-gram order (default 2)")
    ap.add_argument("--count", type=int, default=150, help="tokens to generate")
    ap.add_argument("--temperature", type=float, default=0.8,
                    help="0=most likely, >1=more random (default 0.8)")
    ap.add_argument("--seed", type=int, default=None, help="RNG seed (reproducible)")
    args = ap.parse_args()

    text = sys.stdin.read() if not sys.stdin.isatty() else SAMPLE_CORPUS
    tokens = tokenize(text)
    if args.order < 1:
        sys.exit("--order must be >= 1")
    if len(tokens) <= args.order:
        sys.exit("corpus too small for the requested order")

    table = build_table(tokens, args.order)
    print(generate(table, args.order, args.count, args.temperature, args.seed))


if __name__ == "__main__":
    main()
