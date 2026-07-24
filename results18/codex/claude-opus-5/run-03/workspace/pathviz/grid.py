"""Grid model shared by the maze generators, searches and renderer."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Iterator

WALL = 0
FLOOR = 1

Cell = tuple[int, int]


@dataclass
class Grid:
    """A rectangular grid of walls and weighted floor cells.

    Coordinates are ``(x, y)`` with ``x`` growing right and ``y`` growing down.
    ``weights[y][x]`` is the cost of *entering* that cell; walls have no cost
    because they can never be entered.
    """

    width: int
    height: int
    cells: list[list[int]] = field(default_factory=list)
    weights: list[list[int]] = field(default_factory=list)
    start: Cell = (0, 0)
    goal: Cell = (0, 0)

    def __post_init__(self) -> None:
        if self.width < 1 or self.height < 1:
            raise ValueError("grid must be at least 1x1")
        if not self.cells:
            self.cells = [[WALL] * self.width for _ in range(self.height)]
        if not self.weights:
            self.weights = [[1] * self.width for _ in range(self.height)]
        if len(self.cells) != self.height or any(len(row) != self.width for row in self.cells):
            raise ValueError("cells do not match grid dimensions")
        if len(self.weights) != self.height or any(len(row) != self.width for row in self.weights):
            raise ValueError("weights do not match grid dimensions")

    # -- queries ---------------------------------------------------------
    def in_bounds(self, cell: Cell) -> bool:
        x, y = cell
        return 0 <= x < self.width and 0 <= y < self.height

    def is_floor(self, cell: Cell) -> bool:
        x, y = cell
        return self.in_bounds(cell) and self.cells[y][x] == FLOOR

    def weight(self, cell: Cell) -> int:
        x, y = cell
        return self.weights[y][x]

    def neighbors(self, cell: Cell) -> list[Cell]:
        """Walkable orthogonal neighbors in a stable N, E, S, W order."""
        x, y = cell
        candidates = ((x, y - 1), (x + 1, y), (x, y + 1), (x - 1, y))
        return [c for c in candidates if self.is_floor(c)]

    def floors(self) -> Iterator[Cell]:
        for y in range(self.height):
            for x in range(self.width):
                if self.cells[y][x] == FLOOR:
                    yield (x, y)

    # -- mutation --------------------------------------------------------
    def carve(self, cell: Cell, weight: int = 1) -> None:
        if not self.in_bounds(cell):
            raise ValueError(f"cell {cell} is out of bounds")
        x, y = cell
        self.cells[y][x] = FLOOR
        self.set_weight(cell, weight)

    def set_weight(self, cell: Cell, weight: int) -> None:
        if weight < 1:
            raise ValueError("weights must be >= 1")
        x, y = cell
        self.weights[y][x] = weight

    def path_cost(self, path: list[Cell]) -> int:
        """Total cost of walking ``path``, excluding the starting cell."""
        return sum(self.weight(cell) for cell in path[1:])
