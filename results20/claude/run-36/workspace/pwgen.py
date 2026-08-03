#!/usr/bin/env python3
"""pwgen - a secure password & passphrase generator.

Generates random passwords (random characters) and passphrases (random
words joined by a separator) driven by the operating system's cryptographic
random source (secrets / /dev/urandom). Provides an entropy analysis of what
it produces.

This is a *generator*: it does not guess strength the way a cracker would,
but for a process with a known character set and length, the entropy is
exactly log2(characters ** length), which is what a pure brute-force attack
must walk. Weakness in a real password almost always comes from using a
predictable pattern (dictionary word + year, leetspeak, known name) *and*
keeping that pattern; this tool's job is the complement - a uniform random
draw, so the theoretical entropy is real. See the `estimate` subcommand for
a heuristic of common human patterns.

Exit codes: 0 on success, 1 on argument errors, 2 on misuse.
"""

from __future__ import annotations

import argparse
import math
import secrets
import sys
from dataclasses import dataclass

# Character sets. We deliberately use each byte once so the uniform draw
# over the set maps 1:1 to "guessable symbols" for entropy accounting.
LOWER = "abcdefghijklmnopqrstuvwxyz"
UPPER = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
DIGITS = "0123456789"
SYMBOLS = "!@#$%^&*()-_=+[]{};:,.?/"

# Common English words used for passphrases. Short, unambiguous, and
# non-word-processed so they are easy to type and remember. The entropy math
# relies on this full list being known to the attacker, so we count the
# actual list length, not a fixed 7776 (Diceware) number.
WORDS = """apple
brick
crane
drum
eagle
flame
grape
harbor
island
jolly
kite
lunar
meadow
noble
orbit
piano
quartz
raven
spark
tiger
ultra
vivid
winter
yacht
zebra""".split()

AMBIGUOUS = "0O1lI|"


def urandom_int(n: int) -> int:
    """Return a uniform integer in [0, n).

    Uses rejection sampling over bytes from secrets (CSPRNG) so the result
    is unbiased even when n is not a power of two.
    """
    # smallest power-of-two range that covers [0, n)
    n_bits = n.bit_length()
    # mask off the top bits: max value representable in n_bits
    limit = (1 << n_bits) - 1
    while True:
        x = int.from_bytes(secrets.token_bytes((n_bits + 7) // 8), "big")
        x &= limit
        if x < n:
            return x


def pick(alphabet: str) -> str:
    """Return one random character from `alphabet` (uniform, unbiased)."""
    return alphabet[urandom_int(len(alphabet))]


@dataclass
class GenerateResult:
    value: str
    charset_size: int
    length: int

    @property
    def entropy_bits(self) -> float:
        return self.length * math.log2(self.charset_size)


def generate_password(length: int, *, lower=True, upper=True, digits=True,
                      symbols=True, exclude_ambiguous=False, at_least_one=True) -> str:
    """Build a random password of `length` chars from the requested classes."""
    alphabet = ""
    if lower:
        alphabet += LOWER
    if upper:
        alphabet += UPPER
    if digits:
        alphabet += DIGITS
    if symbols:
        alphabet += SYMBOLS
    if not alphabet:
        raise ValueError("at least one character class must be enabled")

    if exclude_ambiguous:
        alphabet = "".join(c for c in alphabet if c not in AMBIGUOUS)

    # Force at least one char from each class (when the class is enabled),
    # i.e. the "has a digit / has a symbol" guarantees that real-world
    # password policies want. Uses shuffle_guarantee per class then a final
    # shuffle so the result is still uniformly random over the constrained
    # space.
    if at_least_one and length >= 4:
        # One reserved slot per enabled class so the "has a digit / has a
        # symbol" guarantees hold, then fill the rest uniformly and do a
        # final shuffle so the result is still uniform over the constrained
        # space (every position equally likely to hold any class char).
        parts: list[str] = []
        for class_str in (LOWER, UPPER, DIGITS, SYMBOLS):
            if class_str and all(c in alphabet for c in class_str):
                parts.append(pick(class_str))
        parts.extend(pick(alphabet) for _ in range(length - len(parts)))
        for i in range(len(parts) - 1, 0, -1):
            j = urandom_int(i + 1)
            parts[i], parts[j] = parts[j], parts[i]
        value = "".join(parts)
    else:
        value = "".join(pick(alphabet) for _ in range(length))

    return GenerateResult(value, len(alphabet), length)


def generate_passphrase(word_count: int, *, separator="-", title=False) -> GenerateResult:
    """Build a passphrase of `word_count` random words joined by `separator`."""
    n = len(WORDS)
    words = [WORDS[urandom_int(n)] for _ in range(word_count)]
    if title:
        words = [w.capitalize() for w in words]
    return GenerateResult(separator.join(words), n, word_count)


# ---------------------------------------------------------------------------
# Heuristic estimation of the effective entropy of an *existing* password.
# This is a guesser's model, not a guarantee: real attackers know common
# patterns. It deliberately over-counts when no pattern is detected, so treat
# the result as an upper bound, not the truth.
# ---------------------------------------------------------------------------

# Approximate size of a small/common dictionary an attacker would try first.
# Deliberately not the passphrase WORDS list above (that one is *known* to the
# attacker and counted exactly); this models the guesser trying a generic
# common-word dictionary.
_COMMON_WORDS = 10_000


def estimate_strength(password: str) -> dict:
    """Heuristic effective-entropy estimate in bits, plus an assessment.

    Model: an attacker first tries a common-word dictionary (10k words) and
    digit suffixes, then falls back to brute force over printable ASCII. We
    score the dictionary search space when the password looks like words —
    either multiple word tokens (a passphrase), or a single word with a digit
    suffix (the notorious "password123" pattern). A long single token with no
    digit suffix is treated as random, since that is just as likely to be a
    randomly drawn alnum string.

    This is an *upper bound*: real human patterns (leetspeak, a name + birth
    year, one dictionary word spelled out) are almost always weaker than this
    model assumes. Treat the result as optimistic, not definitive.
    """
    # Each alnum token -> (alpha part, trailing digit part).
    pieces = []
    for tok in _split(password):
        m = len(tok)
        while m > 0 and tok[m - 1].isdigit():
            m -= 1
        pieces.append((tok[:m], tok[m:]))

    wordish = [a for a, _ in pieces if _is_wordish(a)]
    dict_pattern = (
        len(wordish) >= 2
        or (len(wordish) == 1 and any(d for a, d in pieces if a in wordish
                                     and d))
    )

    if dict_pattern:
        # Words contribute log2(wordlist) each; digit suffixes contribute
        # log2(10) per digit (plus the separator-free concat is free).
        effective = sum(math.log2(_COMMON_WORDS) for a in wordish)
        effective += sum(len(d) * math.log2(10) for _, d in pieces if d)
        note = "dictionary-derived (common-word list)"
        space = _COMMON_WORDS
    else:
        effective = len(password) * math.log2(95)
        note = "assumed-uniform-random (upper bound)"
        space = 95

    return {"entropy_bits": effective, "space": space, "note": note}


def _split(s: str):
    """Split a password into alnum runs (keeps only alnum runs of len>=1)."""
    import re

    return re.findall(r"[A-Za-z0-9]+", s)


def _is_wordish(tok: str) -> bool:
    """Cheap heuristic: is a bare token plausibly a natural word?"""
    # Markov-ish proxy: reject obvious digit-heavy/leet tokens
    digits = sum(c.isdigit() for c in tok)
    if tok and digits / len(tok) > 0.4:
        return False
    return len(tok) >= 3 and tok.isalpha()


def cmd_generate(args) -> int:
    g = generate_password(
        args.length,
        lower=True,
        upper=not args.no_upper,
        digits=not args.no_digits,
        symbols=not args.no_symbols,
        exclude_ambiguous=args.exclude_ambiguous,
        at_least_one=not args.no_guarantee,
    )
    if args.estimate:
        est = estimate_strength(g.value)
    print(g.value)
    if args.annotation or args.estimate:
        print(f"  entropy: {g.entropy_bits:.1f} bits "
              f"({g.charset_size}^{g.length})", file=sys.stderr)
    if args.estimate:
        print(f"  heuristic: {est['entropy_bits']:.1f} bits "
              f"({est['note']})", file=sys.stderr)
    return 0


def cmd_passphrase(args) -> int:
    g = generate_passphrase(args.words, separator=args.separator,
                            title=args.title)
    print(g.value)
    if args.annotation:
        print(f"  entropy: {g.entropy_bits:.1f} bits "
              f"({g.charset_size}^{g.length} wordlist)", file=sys.stderr)
    return 0


def cmd_estimate(args) -> int:
    est = estimate_strength(args.password)
    print(f"{est['entropy_bits']:.1f} bits")
    print(f"  model: {est['note']} (space={est['space']})")
    return 0


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="pwgen",
        description="Generate secure passwords and passphrases.",
    )
    sub = p.add_subparsers(dest="command", required=True)

    gen = sub.add_parser("pw", help="generate a random password")
    gen.add_argument("-l", "--length", type=int, default=18)
    gen.add_argument("--no-upper", action="store_true", help="exclude uppercase")
    gen.add_argument("--no-digits", action="store_true", help="exclude digits")
    gen.add_argument("--no-symbols", action="store_true", help="exclude symbols")
    gen.add_argument("--no-guarantee", action="store_true",
                     help="drop the 'at least one of each class' guarantee")
    gen.add_argument("--exclude-ambiguous", action="store_true",
                     help=f"exclude ambiguous chars: {AMBIGUOUS!r}")
    gen.add_argument("--estimate", action="store_true",
                     help="also print a heuristic strength estimate")
    gen.add_argument("-a", "--annotation", action="store_true",
                     help="print entropy to stderr")
    gen.set_defaults(func=cmd_generate)

    ph = sub.add_parser("phrase", help="generate a passphrase")
    ph.add_argument("-w", "--words", type=int, default=5)
    ph.add_argument("-s", "--separator", default="-")
    ph.add_argument("-t", "--title", action="store_true", help="capitalise words")
    ph.add_argument("-a", "--annotation", action="store_true")
    ph.set_defaults(func=cmd_passphrase)

    est = sub.add_parser("estimate", help="heuristic strength of an existing password")
    est.add_argument("password")
    est.set_defaults(func=cmd_estimate)

    return p


def main(argv=None) -> int:
    parser = build_parser()
    try:
        args = parser.parse_args(argv)
    except SystemExit as e:
        return int(e.code) if e.code is not None else 1
    args.func(args)
    return 0


if __name__ == "__main__":
    sys.exit(main())
