"""Core Conway's Game of Life engine.

The board is an infinite, sparse grid represented as a set of live-cell
coordinates. This keeps memory usage proportional to the number of live
cells rather than the size of any bounding box, so patterns like gliders
can wander forever without the board needing to grow explicitly.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Iterable, Iterator

Cell = tuple[int, int]


@dataclass
class Board:
    """A Game of Life board tracked as a set of live cell coordinates."""

    cells: set[Cell] = field(default_factory=set)

    @classmethod
    def from_coordinates(cls, coordinates: Iterable[Cell]) -> "Board":
        """Build a board from an iterable of (x, y) live-cell coordinates."""
        return cls(set(coordinates))

    def __len__(self) -> int:
        return len(self.cells)

    def __contains__(self, cell: Cell) -> bool:
        return cell in self.cells

    def __iter__(self) -> Iterator[Cell]:
        return iter(self.cells)

    @staticmethod
    def neighbors(cell: Cell) -> Iterator[Cell]:
        x, y = cell
        for dx in (-1, 0, 1):
            for dy in (-1, 0, 1):
                if dx or dy:
                    yield (x + dx, y + dy)

    def step(self) -> "Board":
        """Return a new Board advanced by one generation.

        Standard Conway rules:
          - A live cell with 2 or 3 live neighbors survives.
          - A dead cell with exactly 3 live neighbors is born.
          - All other cells die or stay dead.
        """
        neighbor_counts: dict[Cell, int] = {}
        for cell in self.cells:
            for neighbor in self.neighbors(cell):
                neighbor_counts[neighbor] = neighbor_counts.get(neighbor, 0) + 1

        next_cells = {
            cell
            for cell, count in neighbor_counts.items()
            if count == 3 or (count == 2 and cell in self.cells)
        }
        return Board(next_cells)

    def bounding_box(self) -> tuple[int, int, int, int] | None:
        """Return (min_x, min_y, max_x, max_y) covering all live cells."""
        if not self.cells:
            return None
        xs = [x for x, _ in self.cells]
        ys = [y for _, y in self.cells]
        return min(xs), min(ys), max(xs), max(ys)

    def translated(self, dx: int, dy: int) -> "Board":
        """Return a new board with every cell shifted by (dx, dy)."""
        return Board({(x + dx, y + dy) for x, y in self.cells})
