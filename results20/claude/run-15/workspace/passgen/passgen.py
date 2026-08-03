#!/usr/bin/env python3
"""passgen — a small, cryptographic-grade password & passphrase generator.

Uses `secrets` (CSPRNG) exclusively so the output is never predictable.

Two modes:
  * Password   — a string of random characters from a chosen alphabet.
  * Passphrase — a sequence of words from the embedded EFF word list joined
                 by a separator, giving X bits of entropy with memorable output.

No dependencies beyond the standard library.
"""

from __future__ import annotations

import argparse
import secrets
import string
import sys

# Default alphabets
LOWERCASE = string.ascii_lowercase
UPPERCASE = string.ascii_uppercase
DIGITS = string.digits
SYMBOLS = "!@#$%^&*()-_=+[]{};:,.<>?"

# The EFF "long word list" (7,776 words, ~12.9 bits of entropy each) has
# permissive licensing. Rather than embedding all 7,776, we keep a curated
# subset here so the module is self-contained and lightweight.
_DEFAULT_WORDS = [
    "abacus", "absurd", "acorn", "across", "admiral", "adrift", "agenda",
    "alarm", "alpine", "amber", "anchor", "anthem", "anyway", "apron",
    "arcade", "arctic", "asylum", "atlas", "atomic", "aurora", "autumn",
    "avocado", "backdrop", "badge", "bamboo", "banner", "barley", "basin",
    "batter", "beacon", "beetle", "bingo", "bishop", "blizzard", "blossom",
    "bonus", "boulder", "bracket", "breeze", "briar", "bronze", "brooch",
    "buckle", "buffalo", "calico", "canyon", "cargo", "castle", "caviar",
    "cedar", "chalk", "cherry", "circus", "clover", "cobalt", "comet",
    "copper", "coral", "cotton", "cricket", "crimson", "crystal", "cuisine",
    "dahlia", "daisy", "danube", "delta", "denim", "diamond", "dinghy",
    "dolphin", "drizzle", "duckling", "eagle", "echo", "eden", "ember",
    "emerald", "falcon", "feather", "ferret", "fiesta", "fir", "flamingo",
    "flurry", "foxtrot", "frost", "gadget", "galaxy", "gazelle", "geyser",
    "ginger", "glacier", "granite", "grape", "griffin", "guitar", "harbor",
    "harvest", "hazel", "heather", "heron", "hinge", "holly", "honey",
    "horizon", "huckle", "hunter", "ibis", "igloo", "indigo", "iris", "ivory",
    "jackal", "jade", "jaguar", "janice", "jasmine", "jigsaw", "jovial",
    "juniper", "kayak", "kelvin", "kernel", "kettle", "kiwi", "koala",
    "kraken", "ladle", "lagoon", "lantern", "latitude", "lattice", "lazuli",
    "lemur", "lichen", "lilac", "limber", "linden", "linen", "locust",
    "lotus", "luggage", "lumen", "lynx", "magnet", "malachite", "marigold",
    "meadow", "medley", "mesa", "meteor", "mimosa", "mint", "mirror",
    "mosaic", "murmur", "mystic", "napkin", "nebula", "nickel", "noodle",
    "nostril", "oak", "obelisk", "octagon", "olive", "onyx", "orange",
    "orchid", "otter", "oyster", "panda", "papaya", "parrot", "pebble",
    "peony", "pepper", "petal", "phoenix", "pigeon", "pillow", "pine",
    "plum", "poppy", "prairie", "prism", "puffin", "purple", "puzzle",
    "quail", "quartz", "quill", "quiet", "quiver", "rabbit", "radiant",
    "raven", "recess", "reed", "rhino", "rifle", "riverside", "robin",
    "rose", "ruby", "saffron", "sapphire", "scarab", "sequoia", "shadow",
    "silver", "skylark", "slate", "sparrow", "spring", "squirrel", "stone",
    "stream", "summit", "sunflower", "tangerine", "teak", "thistle", "tiger",
    "topaz", "toucan", "trail", "trout", "tulip", "tundra", "tusk", "umbrella",
    "utopia", "valley", "velvet", "vermillion", "violet", "walnut", "weasel",
    "whale", "willow", "winter", "wolf", "wombat", "yellow", "zeal", "zebra",
    "zinc", "zircon",
]

def entropy_length_required(pool_size: int, bits: float) -> int:
    """Smallest length N such that pool_size**N >= 2**bits."""
    import math

    return max(1, math.ceil(bits / math.log2(pool_size)))


def generate_password(length: int = 16, *, lower: bool = True, upper: bool = True,
                      digits: bool = True, symbols: bool = False) -> str:
    """Generate a random password of the requested length.

    Guarantees at least one character from each enabled class (so a password
    that claims to include symbols always does), then fills the rest randomly.
    """
    pools: list[str] = []
    if lower:
        pools.append(LOWERCASE)
    if upper:
        pools.append(UPPERCASE)
    if digits:
        pools.append(DIGITS)
    if symbols:
        pools.append(SYMBOLS)

    if not pools:
        raise ValueError("at least one character class must be enabled")

    if length < len(pools):
        raise ValueError(
            f"length {length} is too short to include all enabled classes "
            f"({len(pools)})"
        )

    # One guaranteed character per class, then random fill from the union.
    guaranteed = [secrets.choice(p) for p in pools]
    union = "".join(pools)
    rest = [secrets.choice(union) for _ in range(length - len(pools))]
    chars = guaranteed + rest
    secrets.SystemRandom().shuffle(chars)
    return "".join(chars)


def generate_passphrase(words: int = 6, *, separator: str = " ") -> str:
    """Generate a random passphrase of N words from the word list."""
    if words < 1:
        raise ValueError("word count must be >= 1")
    return separator.join(secrets.choice(_DEFAULT_WORDS) for _ in range(words))


def password_entropy(__password: str, *, lower: bool, upper: bool,
                     digits: bool, symbols: bool) -> float:
    """Entropy in bits = length * log2(pool size), assuming uniform random."""
    import math

    pool = 0
    if lower:
        pool += len(LOWERCASE)
    if upper:
        pool += len(UPPERCASE)
    if digits:
        pool += len(DIGITS)
    if symbols:
        pool += len(SYMBOLS)
    return len(__password) * math.log2(pool)


def passphrase_entropy(word_count: int) -> float:
    """Bits of entropy in a passphrase = words * log2(len(word_list))."""
    import math

    return word_count * math.log2(len(_DEFAULT_WORDS))


def _build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="passgen",
        description="Generate cryptographic-grade passwords and passphrases.",
    )
    sub = p.add_subparsers(dest="mode", required=True)

    pw = sub.add_parser("password", help="generate a random character password")
    pw.add_argument("-l", "--length", type=int, default=16,
                    help="length (default: 16)")
    pw.add_argument("--no-lower", action="store_true", help="exclude lowercase")
    pw.add_argument("--no-upper", action="store_true", help="exclude uppercase")
    pw.add_argument("--no-digits", action="store_true", help="exclude digits")
    pw.add_argument("-s", "--symbols", action="store_true",
                    help="include !@#$%^&*()... symbols")
    pw.add_argument("--entropy", type=float, default=None,
                    help="generate the shortest password with >= this many bits")

    ph = sub.add_parser("passphrase", help="generate a random word passphrase")
    ph.add_argument("-w", "--words", type=int, default=6,
                    help="number of words (default: 6)")
    ph.add_argument("--separator", default=" ",
                    help="word separator (default: space)")
    ph.add_argument("--entropy", type=float, default=None,
                    help="generate the fewest words with >= this many bits")

    return p


def main(argv: list[str] | None = None) -> int:
    args = _build_parser().parse_args(argv)

    try:
        if args.mode == "password":
            # Character classes are on, unless explicitly disabled.
            lower = not args.no_lower
            upper = not args.no_upper
            digits = not args.no_digits
            symbols = args.symbols

            length = args.length
            if args.entropy is not None:
                pool = len(LOWERCASE) if lower else 0
                pool += len(UPPERCASE) if upper else 0
                pool += len(DIGITS) if digits else 0
                pool += len(SYMBOLS) if symbols else 0
                length = entropy_length_required(pool, args.entropy)
            print(generate_password(length, lower=lower, upper=upper,
                                    digits=digits, symbols=symbols))
        elif args.mode == "passphrase":
            words = args.words
            if args.entropy is not None:
                import math

                words = max(1, math.ceil(args.entropy / math.log2(len(_DEFAULT_WORDS))))
            print(generate_passphrase(words, separator=args.separator))
    except ValueError as exc:
        print(f"passgen: error: {exc}", file=sys.stderr)
        return 2

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
