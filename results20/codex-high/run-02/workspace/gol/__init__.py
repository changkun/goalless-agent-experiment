"""Conway's Game of Life — engine + CLI."""

from .engine import Grid, neighbors, next_generation, parse, render, blinker, glider

__all__ = [
    "Grid",
    "neighbors",
    "next_generation",
    "parse",
    "render",
    "blinker",
    "glider",
]

__version__ = "0.1.0"
