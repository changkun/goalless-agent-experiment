"""Conway's Game of Life — a zero-dependency Python implementation."""

from .engine import (
    Game,
    next_generation,
    parse_pattern,
    render,
    PRESETS,
)

__all__ = [
    "Game",
    "next_generation",
    "parse_pattern",
    "render",
    "PRESETS",
]
