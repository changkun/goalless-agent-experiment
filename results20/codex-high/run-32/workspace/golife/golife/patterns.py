"""A small collection of classic Game of Life patterns."""
from __future__ import annotations

from .engine import Pattern

PATTERNS: dict[str, Pattern] = {}


def _register(name: str, rows: str) -> None:
    PATTERNS[name] = Pattern(name=name, rows=tuple(rows.strip("\n").splitlines()))


PATTERNS["block"] = Pattern("block", ("**", "**"))

_register("beehive", """
.**
*..*
.**""")

_register("blinker", """
***
""")

_register("toad", """
.***
***.
""")

_register("beacon", """
**..
**..
..**
..**
""")

_register("glider", """
.*.
..*
***
""")

_register("lwss", """
.****
*...*
....*
*..*.
""")

_register("r_pentomino", """
.##
##.
.#.
""")

_register("pulsar", """
..***..***..
............
*....*.*....*
*....*.*....*
*....*.*....*
..***..***..
............
*....*.*....*
*....*.*....*
*....*.*....*
..***..***..
............
..***..***..
""")


def list_patterns() -> list[str]:
    return sorted(PATTERNS)


def get(pattern: str) -> Pattern:
    key = pattern.lower().replace("-", "_").replace(" ", "_")
    if key not in PATTERNS:
        raise KeyError(
            f"unknown pattern {pattern!r}; choose from: {', '.join(list_patterns())}"
        )
    return PATTERNS[key]
