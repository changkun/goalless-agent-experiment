"""Demo CLI: print a random bird fact and a little ASCII bird.

A tiny, dependency-free Python script I put together since the workspace
was empty. Run it with:

    python3 birdfacts.py
    python3 birdfacts.py --count 3
"""
from __future__ import annotations

import argparse
import random
import sys

FACTS = [
    "A group of owls is called a parliament.",
    "Hornbills seal their nests with mud, leaving only a small slit.",
    "The Arctic tern migrates farther than any other bird each year.",
    "Some songbirds learn their tunes by listening to older neighbors.",
    "A hummingbird can beat its wings dozens of times every second.",
    "Puffins can hold many small fish in their beaks at once.",
    "Crows are known to recognize individual human faces.",
    "The kiwi is flightless and has nostrils at the tip of its beak.",
]

BIRD = r"""
       ___
     <(o )___
      ( ._> /
       `---'
    tweet!
"""


def main() -> int:
    parser = argparse.ArgumentParser(description="A tiny bird-facts CLI.")
    parser.add_argument(
        "--count",
        type=int,
        default=1,
        help="How many facts to print (default: 1).",
    )
    args = parser.parse_args()

    if args.count < 1:
        print("Count must be at least 1.", file=sys.stderr)
        return 1

    facts = random.sample(FACTS, k=min(args.count, len(FACTS)))
    print(BIRD)
    for fact in facts:
        print(f"- {fact}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
