"""Core Conway's Game of Life logic.

The board is represented as a sparse set of (row, col) coordinates for
live cells. This lets the grid grow unbounded in any direction, which
is a nicer fit for the "infinite plane" rules of the game than a fixed
2D array.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Iterable, Set, Tuple

Cell = Tuple[int, int]

_NEIGHBOR_OFFSETS: Tuple[Cell, ...] = tuple(
    (dr, dc)
    for dr in (-1, 0, 1)
    for dc in (-1, 0, 1)
    if (dr, dc) != (0, 0)
)


@dataclass
class Board:
    """Holds the set of live cells and knows how to advance generations."""

    live_cells: Set[Cell] = field(default_factory=set)
    generation: int = 0

    @classmethod
    def from_pattern(cls, pattern: Iterable[str], alive_char: str = "#") -> "Board":
        """Build a board from a list of strings, one per row.

        Each character equal to ``alive_char`` marks a live cell.
        """
        live = {
            (row, col)
            for row, line in enumerate(pattern)
            for col, char in enumerate(line)
            if char == alive_char
        }
        return cls(live_cells=live)

    def neighbors(self, cell: Cell) -> Iterable[Cell]:
        row, col = cell
        for dr, dc in _NEIGHBOR_OFFSETS:
            yield (row + dr, col + dc)

    def live_neighbor_count(self, cell: Cell) -> int:
        return sum(1 for n in self.neighbors(cell) if n in self.live_cells)

    def step(self) -> "Board":
        """Return a new Board representing the next generation.

        Applies the standard rules:
          - A live cell with 2 or 3 live neighbors survives.
          - A dead cell with exactly 3 live neighbors becomes alive.
          - All other cells are dead in the next generation.
        """
        candidates: Set[Cell] = set(self.live_cells)
        for cell in self.live_cells:
            candidates.update(self.neighbors(cell))

        next_live: Set[Cell] = set()
        for cell in candidates:
            count = self.live_neighbor_count(cell)
            if cell in self.live_cells:
                if count in (2, 3):
                    next_live.add(cell)
            elif count == 3:
                next_live.add(cell)

        return Board(live_cells=next_live, generation=self.generation + 1)

    def bounding_box(self) -> Tuple[int, int, int, int]:
        """Return (min_row, min_col, max_row, max_col) of live cells.

        Raises ValueError if the board has no live cells.
        """
        if not self.live_cells:
            raise ValueError("Board has no live cells")
        rows = [r for r, _ in self.live_cells]
        cols = [c for _, c in self.live_cells]
        return min(rows), min(cols), max(rows), max(cols)

    def render(self, alive_char: str = "#", dead_char: str = ".", padding: int = 0) -> str:
        """Render the current live cells as a text grid.

        If the board is empty, returns an empty string.
        """
        if not self.live_cells:
            return ""

        min_row, min_col, max_row, max_col = self.bounding_box()
        min_row -= padding
        min_col -= padding
        max_row += padding
        max_col += padding

        lines = []
        for row in range(min_row, max_row + 1):
            line = "".join(
                alive_char if (row, col) in self.live_cells else dead_char
                for col in range(min_col, max_col + 1)
            )
            lines.append(line)
        return "\n".join(lines)

    def __len__(self) -> int:
        return len(self.live_cells)
