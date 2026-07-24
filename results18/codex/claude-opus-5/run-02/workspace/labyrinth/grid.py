"""Grid of cells connected by carved passages."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Iterator

NORTH = (-1, 0)
SOUTH = (1, 0)
EAST = (0, 1)
WEST = (0, -1)
DIRECTIONS = (NORTH, EAST, SOUTH, WEST)

Cell = tuple[int, int]


@dataclass
class Grid:
    """A rectangular maze grid.

    Cells are ``(row, col)`` pairs. Two adjacent cells are "linked" when the
    wall between them has been carved away.
    """

    height: int
    width: int
    _links: dict[Cell, set[Cell]] = field(default_factory=dict, repr=False)

    def __post_init__(self) -> None:
        if self.height < 1 or self.width < 1:
            raise ValueError("grid must be at least 1x1")
        self._links = {cell: set() for cell in self.cells()}

    def cells(self) -> Iterator[Cell]:
        for row in range(self.height):
            for col in range(self.width):
                yield (row, col)

    def __len__(self) -> int:
        return self.height * self.width

    def contains(self, cell: Cell) -> bool:
        row, col = cell
        return 0 <= row < self.height and 0 <= col < self.width

    def neighbors(self, cell: Cell) -> list[Cell]:
        """All in-bounds adjacent cells, regardless of walls."""
        row, col = cell
        return [
            (row + dr, col + dc)
            for dr, dc in DIRECTIONS
            if self.contains((row + dr, col + dc))
        ]

    def link(self, a: Cell, b: Cell) -> None:
        """Carve the wall between two adjacent cells."""
        if b not in self.neighbors(a):
            raise ValueError(f"{a} and {b} are not adjacent")
        self._links[a].add(b)
        self._links[b].add(a)

    def unlink(self, a: Cell, b: Cell) -> None:
        self._links[a].discard(b)
        self._links[b].discard(a)

    def linked(self, a: Cell, b: Cell) -> bool:
        return b in self._links.get(a, ())

    def passages(self, cell: Cell) -> set[Cell]:
        """Neighbors reachable from ``cell`` without crossing a wall."""
        return set(self._links[cell])

    def edges(self) -> Iterator[tuple[Cell, Cell]]:
        """Each carved passage once, in a stable order."""
        for cell in self.cells():
            for other in sorted(self._links[cell]):
                if cell < other:
                    yield (cell, other)

    def has_wall(self, cell: Cell, direction: tuple[int, int]) -> bool:
        """True when a wall separates ``cell`` from its neighbor in ``direction``."""
        row, col = cell
        other = (row + direction[0], col + direction[1])
        if not self.contains(other):
            return True
        return not self.linked(cell, other)
