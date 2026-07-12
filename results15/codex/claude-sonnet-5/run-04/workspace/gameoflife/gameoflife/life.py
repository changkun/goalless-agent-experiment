"""Core Game of Life logic: a Board class with an infinite, sparse grid."""

from __future__ import annotations

from typing import Iterable, Set, Tuple

Cell = Tuple[int, int]

_NEIGHBOR_OFFSETS: Tuple[Cell, ...] = (
    (-1, -1), (-1, 0), (-1, 1),
    (0, -1),           (0, 1),
    (1, -1),  (1, 0),  (1, 1),
)


class Board:
    """Represents a Game of Life board on an unbounded grid.

    Only living cells are stored, so the board can grow in any direction
    without needing to know its size in advance.
    """

    def __init__(self, alive_cells: Iterable[Cell] = ()) -> None:
        self._alive: Set[Cell] = set(alive_cells)

    @classmethod
    def from_pattern(cls, pattern: str, alive_char: str = "#") -> "Board":
        """Build a board from a multi-line string pattern.

        Each line represents a row; ``alive_char`` marks a living cell.
        Leading/trailing blank lines are stripped.
        """
        lines = pattern.strip("\n").split("\n")
        alive = {
            (row, col)
            for row, line in enumerate(lines)
            for col, char in enumerate(line)
            if char == alive_char
        }
        return cls(alive)

    @property
    def alive_cells(self) -> Set[Cell]:
        return set(self._alive)

    def is_alive(self, cell: Cell) -> bool:
        return cell in self._alive

    def population(self) -> int:
        return len(self._alive)

    def neighbors(self, cell: Cell) -> Iterable[Cell]:
        row, col = cell
        for dr, dc in _NEIGHBOR_OFFSETS:
            yield (row + dr, col + dc)

    def live_neighbor_count(self, cell: Cell) -> int:
        return sum(1 for n in self.neighbors(cell) if n in self._alive)

    def step(self) -> "Board":
        """Compute and return the next generation as a new Board."""
        candidates: Set[Cell] = set()
        for cell in self._alive:
            candidates.add(cell)
            candidates.update(self.neighbors(cell))

        next_alive: Set[Cell] = set()
        for cell in candidates:
            count = self.live_neighbor_count(cell)
            if cell in self._alive:
                if count in (2, 3):
                    next_alive.add(cell)
            elif count == 3:
                next_alive.add(cell)

        return Board(next_alive)

    def bounds(self) -> Tuple[int, int, int, int]:
        """Return (min_row, min_col, max_row, max_col) of living cells."""
        if not self._alive:
            return (0, 0, 0, 0)
        rows = [r for r, _ in self._alive]
        cols = [c for _, c in self._alive]
        return (min(rows), min(cols), max(rows), max(cols))

    def render(self, alive_char: str = "#", dead_char: str = ".", padding: int = 0) -> str:
        """Render the board as a string within its bounding box."""
        if not self._alive:
            return ""
        min_row, min_col, max_row, max_col = self.bounds()
        min_row -= padding
        min_col -= padding
        max_row += padding
        max_col += padding

        lines = []
        for row in range(min_row, max_row + 1):
            line = "".join(
                alive_char if (row, col) in self._alive else dead_char
                for col in range(min_col, max_col + 1)
            )
            lines.append(line)
        return "\n".join(lines)

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Board):
            return NotImplemented
        return self._alive == other._alive

    def __repr__(self) -> str:
        return f"Board({sorted(self._alive)!r})"
