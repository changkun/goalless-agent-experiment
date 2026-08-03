"""Seed patterns placed at the top-left of the board."""

from collections.abc import Iterable

Cell = tuple[int, int]

BLINKER: Iterable[Cell] = ((1, 1), (1, 2), (1, 3))
BLOCK: Iterable[Cell] = ((1, 1), (1, 2), (2, 1), (2, 2))
GLIDER: Iterable[Cell] = ((1, 2), (2, 3), (3, 1), (3, 2), (3, 3))
