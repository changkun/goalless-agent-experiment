"""Core password generation and strength analysis logic (no external deps)."""

from __future__ import annotations

import math
import re
import secrets
import string

# Character set groups. Using "similar" characters can be excluded to keep
# generated passwords unambiguous when typed by hand.
LOWER = string.ascii_lowercase
UPPER = string.ascii_uppercase
DIGITS = string.digits
SYMBOLS = "!@#$%^&*()-_=+[]{};:,.<>?"
AMBIGUOUS = "Il1O0o"


class StrengthError(ValueError):
    """Raised when a requested generation is impossible to satisfy."""


def analyze_strength(password: str) -> dict:
    """Return a dict describing the entropy and complexity of a password."""
    if not password:
        raise ValueError("password must not be empty")

    length = len(password)
    pool = 0
    if any(c in LOWER for c in password):
        pool += len(LOWER)
    if any(c in UPPER for c in password):
        pool += len(UPPER)
    if any(c in DIGITS for c in password):
        pool += len(DIGITS)
    if any(c in SYMBOLS for c in password):
        pool += len(SYMBOLS)

    entropy = length * math.log2(pool) if pool else 0.0

    checks = {
        "lowercase": bool(re.search(r"[a-z]", password)),
        "uppercase": bool(re.search(r"[A-Z]", password)),
        "digits": bool(re.search(r"\d", password)),
        "symbols": bool(re.search(r"[^A-Za-z0-9]", password)),
    }
    score = sum(1 for v in checks.values() if v)
    rounds = min(score, 2) + (1 if length >= 8 else 0) + (1 if length >= 12 else 0)

    if entropy < 30:
        grade = "very weak"
    elif entropy < 50:
        grade = "weak"
    elif entropy < 70:
        grade = "moderate"
    elif entropy < 100:
        grade = "strong"
    else:
        grade = "very strong"

    return {
        "length": length,
        "pool_size": pool,
        "entropy_bits": round(entropy, 1),
        "charset_used": checks,
        "score": score,
        "strength_rounds": rounds,
        "grade": grade,
    }


def generate_password(
    length: int = 16,
    lowercase: bool = True,
    uppercase: bool = True,
    digits: bool = True,
    symbols: bool = True,
    exclude_ambiguous: bool = False,
) -> str:
    """Generate a cryptographically secure random password.

    Uses ``secrets`` so output is suitable for authentication material.
    """
    include_groups: list[str] = []
    if lowercase:
        include_groups.append(LOWER)
    if uppercase:
        include_groups.append(UPPER)
    if digits:
        include_groups.append(DIGITS)
    if symbols:
        include_groups.append(SYMBOLS)

    if not include_groups:
        raise StrengthError("at least one character group must be enabled")

    if length < len(include_groups):
        raise StrengthError(
            f"length must be >= number of enabled groups ({len(include_groups)})"
        )

    pool = "".join(include_groups)
    if exclude_ambiguous:
        pool = "".join(c for c in pool if c not in AMBIGUOUS)

    if not pool:
        raise StrengthError("character pool is empty after exclusions")

    # Guarantee at least one character from each requested group so the full
    # pool is actually represented, then fill the rest randomly.
    password = [secrets.choice(g) for g in include_groups]
    for _ in range(length - len(password)):
        password.append(secrets.choice(pool))

    secrets.SystemRandom().shuffle(password)
    return "".join(password)
