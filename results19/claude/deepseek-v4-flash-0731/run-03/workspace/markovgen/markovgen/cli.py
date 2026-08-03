"""Command-line interface for markovgen."""

from __future__ import annotations

import argparse
import random
import sys
from pathlib import Path

from .chain import MarkovChain


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="markovgen",
        description="Generate text with an order-N Markov chain learned from example text.",
    )
    parser.add_argument(
        "corpus",
        nargs="*",
        type=Path,
        help="Text file(s) to learn from. Reads stdin if none are given.",
    )
    parser.add_argument(
        "-n",
        "--order",
        type=int,
        default=2,
        metavar="N",
        help="Markov chain order (number of context tokens), default 2.",
    )
    parser.add_argument(
        "-l",
        "--length",
        type=int,
        default=50,
        metavar="N",
        help="Number of tokens to generate, default 50.",
    )
    parser.add_argument(
        "-s",
        "--seed-tokens",
        nargs="+",
        metavar="TOKEN",
        help="Optional starting tokens for generation (greedy by tail match).",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=None,
        metavar="INT",
        help="Random seed for reproducible tie-breaking.",
    )
    return parser


def read_corpus(paths: list[Path]) -> str:
    """Concatenate the given files (or stdin if none) into one document."""
    if not paths:
        return sys.stdin.read()
    parts = []
    for path in paths:
        if not path.is_file():
            sys.stderr.write(f"markovgen: no such file: {path}\n")
            continue
        parts.append(path.read_text(encoding="utf-8"))
    return "\n".join(parts)


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)

    corpus = read_corpus(args.corpus)
    if not corpus.strip():
        sys.stderr.write("markovgen: empty corpus, nothing to learn from\n")
        return 1

    chain = MarkovChain(order=args.order, rng=random.Random(args.seed))
    chain.fit(corpus)

    seed = args.seed_tokens or None
    text = chain.generate(args.length, seed=seed)
    print(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
