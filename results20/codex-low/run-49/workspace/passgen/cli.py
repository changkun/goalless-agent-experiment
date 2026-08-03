"""Command-line interface for the passphrase generator."""
from __future__ import annotations

import argparse
import sys

from passgen.generator import available_words, generate


def main(argv: list[str] | None = None) -> int:
    pool = available_words()
    parser = argparse.ArgumentParser(
        prog="passgen",
        description="Generate a secure, memorable passphrase.",
    )
    parser.add_argument(
        "-n", "--count", type=int, default=6,
        help=f"number of words (pool has {len(pool)} words)",
    )
    parser.add_argument(
        "-s", "--separator", default="-",
        help="character(s) placed between words",
    )
    parser.add_argument(
        "--entropy", action="store_true",
        help="also print the approximate entropy in bits",
    )
    args = parser.parse_args(argv)

    try:
        pp = generate(count=args.count, pool=pool, separator=args.separator)
    except ValueError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2

    print(pp.as_str())
    if args.entropy:
        print(f"(~{pp.entropy_bits:.0f} bits of entropy)", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
