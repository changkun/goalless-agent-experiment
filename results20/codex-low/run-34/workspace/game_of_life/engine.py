"""Core Game of Life logic.

The universe is a set of `(row, col)` coordinates of live cells, which keeps
the engine independent of any particular grid size and fast on sparse boards.
"""

from __future__ import annotations

from collections.abc import Iterable

Cell = tuple[int, int]

# The eight neighbours of a cell, in row-major order.
_NEIGHBOURS = (
    (-1, -1), (-1, 0), (-1, 1),
    (0, -1),           (0, 1),
    (1, -1),  (1, 0),  (1, 1),
)


class Life:
    """A Game of Life universe with a bounded, toroidal board."""

    def __init__(self, width: int, height: int, live: Iterable[Cell] = ()) -> None:
        if width <= 0 or height <= 0:
            raise ValueError("width and height must be positive")
        self.width = width
        self.height = height
        self.live_cells: set[Cell] = {
            (r % height, c % width)
            for r, c in live
            if 0 <= r < height and 0 <= c < width
        }

    def is_alive(self, row: int, col: int) -> bool:
        return (row % self.height, col % self.width) in self.live_cells

    def step(self) -> None:
        """Advance the universe by one generation."""
        counts: dict[Cell, int] = {}
        for row, col in self.live_cells:
            for dr, dc in _NEIGHBOURS:
                neighbour = ((row + dr) % self.height, (col + dc) % self.width)
                counts[neighbour] = counts.get(neighbour, 0) + 1

        surviving = {
            cell for cell, count in counts.items()
            if count == 3 or (count == 2 and cell in self.live_cells)
        }
        self.live_cells = surviving

    def population(self) -> int:
        return len(self.live_cells)
