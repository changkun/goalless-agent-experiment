"""Core generation logic for passgen."""

from __future__ import annotations

import argparse
import math
import secrets
import sys
from typing import List, Optional, Sequence

# A small built-in wordlist covering a useful alphabet range, so the tool
# works out of the box with zero dependencies. 52 words -> 5.7 bits each.
DEFAULT_WORDLIST: Sequence[str] = (
    "amber bass coral daisy eagle falcon ginger harbor iris jade kale "
    "larch maple nickel olive poppy quartz raven slate tiger umber vine "
    "willow yarrow zebra atlas brook climb drift ember fjord gale hush "
    "ivory jolt kelp loom misty nook onyx plume quill ripple summit "
    "tidal under vivid whirl yonder zest"
).split()

# Character sets used for password generation.
LOWERCASE = "abcdefghijklmnopqrstuvwxyz"
UPPERCASE = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
DIGITS = "0123456789"
SYMBOLS = "!@#$%^&*()-_=+[]{};:,.<>?"


def entropy(pool: int, length: int) -> float:
    """Return entropy in bits for *length* draws from a *pool* of size ``pool``."""
    if pool <= 0 or length < 0:
        return 0.0
    return length * math.log2(pool)


def _choose(pool: str) -> str:
    return secrets.choice(pool)


def generate_password(
    length: int = 16,
    *,
    lowercase: bool = True,
    uppercase: bool = True,
    digits: bool = True,
    symbols: bool = True,
    rng: Optional[object] = None,
) -> str:
    """Generate a random password.

    By default all character classes participate. Passing ``rng`` (an object
    with a ``choice`` method) makes generation deterministic for testing.
    """
    if length < 1:
        raise ValueError("length must be >= 1")
    chars = ""
    if lowercase:
        chars += LOWERCASE
    if uppercase:
        chars += UPPERCASE
    if digits:
        chars += DIGITS
    if symbols:
        chars += SYMBOLS
    if not chars:
        raise ValueError("at least one character class must be enabled")

    pick = _choose if rng is None else rng.choice
    return "".join(pick(chars) for _ in range(length))


def generate_passphrase(
    words: int = 5,
    *,
    wordlist: Sequence[str] = DEFAULT_WORDLIST,
    separator: str = "-",
    capitalize: bool = False,
    number: bool = False,
    rng: Optional[object] = None,
) -> str:
    """Generate a passphrase built from randomly chosen words.

    ``number``: append a random 2-digit number for extra security.
    """
    if words < 1:
        raise ValueError("words must be >= 1")
    wordlist = tuple(wordlist)
    if not wordlist:
        raise ValueError("wordlist must not be empty")
    pick = _choose if rng is None else rng.choice

    chosen = [str(pick(wordlist)) for _ in range(words)]
    if capitalize:
        chosen = [w.capitalize() for w in chosen]
    passphrase = separator.join(chosen)
    if number:
        suffix = str(pick(DIGITS)) + str(pick(DIGITS))
        passphrase += separator + suffix
    return passphrase


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="passgen",
        description="Generate strong passphrases or passwords with entropy info.",
    )
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument(
        "--passphrase",
        action="store_true",
        help="generate a passphrase from words (default)",
    )
    mode.add_argument(
        "--password",
        action="store_true",
        help="generate a random password from character classes",
    )

    parser.add_argument("-n", "--count", type=int, default=1, help="number to generate")
    parser.add_argument("-l", "--length", type=int, default=16, help="password length")
    parser.add_argument("-w", "--words", type=int, default=5, help="passphrase word count")
    parser.add_argument(
        "-s", "--separator", default="-", help="passphrase word separator"
    )
    parser.add_argument("--capitalize", action="store_true", help="capitalize passphrase words")
    parser.add_argument("--number", action="store_true", help="append 2 digits to passphrase")
    parser.add_argument("--no-lower", action="store_true", help="password: exclude lowercase")
    parser.add_argument("--no-upper", action="store_true", help="password: exclude uppercase")
    parser.add_argument("--no-digits", action="store_true", help="password: exclude digits")
    parser.add_argument("--no-symbols", action="store_true", help="password: exclude symbols")
    parser.add_argument("-v", "--verbose", action="store_true", help="show entropy for each result")
    parser.add_argument("--version", action="version", version="passgen 0.1.0")
    return parser


def _pool_size(args: argparse.Namespace) -> int:
    size = 0
    if not args.no_lower:
        size += len(LOWERCASE)
    if not args.no_upper:
        size += len(UPPERCASE)
    if not args.no_digits:
        size += len(DIGITS)
    if not args.no_symbols:
        size += len(SYMBOLS)
    return size


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)

    if args.count < 1:
        parser.error("--count must be >= 1")

    for _ in range(args.count):
        if args.password:
            if args.no_lower and args.no_upper and args.no_digits and args.no_symbols:
                parser.error("at least one character class must be enabled")
            value = generate_password(
                args.length,
                lowercase=not args.no_lower,
                uppercase=not args.no_upper,
                digits=not args.no_digits,
                symbols=not args.no_symbols,
            )
            bits = entropy(_pool_size(args), args.length)
        else:
            bits = entropy(len(DEFAULT_WORDLIST), args.words)
            if args.number:
                bits += entropy(100, 1)
            value = generate_passphrase(
                args.words,
                wordlist=DEFAULT_WORDLIST,
                separator=args.separator,
                capitalize=args.capitalize,
                number=args.number,
            )

        if args.verbose:
            print(f"{value}  ({bits:.1f} bits)")
        else:
            print(value)
    return 0


if __name__ == "__main__":
    sys.exit(main())
