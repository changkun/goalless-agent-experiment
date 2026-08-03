"""Curated starting patterns for the Game of Life."""

from __future__ import annotations

from .engine import Board, parse_rle, Point

BLINKER = "3o"
_BLOCK = "2o$2o!"
_GLIDER = "bob$2bo$3o!"
_GOSPER = (
    "24bo$22bobo$12b2o6b2o12b2o$11bo3bo4b2o12b2o$2o8bo5bo3b2o$2o8bo3bob2o4bobo$"
    "10bo5bo7bo$11bo3bo$12b2o!"
)

PATTERNS: dict[str, str] = {
    "block": _BLOCK,
    "blinker": BLINKER,
    "glider": _GLIDER,
    "gosper": _GOSPER,
}


def get_board(name: str) -> Board:
    """Return a board built from a built-in pattern by name.

    Raises ``KeyError`` for unknown patterns.
    """
    if name not in PATTERNS:
        raise KeyError(f"unknown pattern: {name!r}")
    return parse_rle(PATTERNS[name])
