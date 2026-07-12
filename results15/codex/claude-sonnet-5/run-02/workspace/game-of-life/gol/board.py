"""Sparse, unbounded board implementation for Conway's Game of Life.

Instead of a fixed-size grid, the board tracks only the set of live cell
coordinates. This lets patterns grow or shrink without worrying about
running off the edge of a pre-allocated array, and keeps memory usage
proportional to the number of live cells rather than the board area.
"""

from __future__ import annotations

from typing import Iterable, Iterator

Cell = tuple[int, int]


class Board:
    """A Game of Life board backed by a set of live cell coordinates."""

    def __init__(self, live_cells: Iterable[Cell] = ()) -> None:
        self._live: set[Cell] = set(live_cells)

    @classmethod
    def from_pattern(cls, pattern: str, alive: str = "#") -> "Board":
        """Build a board from a multi-line string pattern.

        Each character equal to ``alive`` becomes a live cell; all other
        characters are treated as dead. Leading/trailing blank lines are
        ignored so patterns can be written as indented triple-quoted
        strings.
        """
        lines = pattern.strip("\n").splitlines()
        live = {
            (x, y)
            for y, line in enumerate(lines)
            for x, char in enumerate(line)
            if char == alive
        }
        return cls(live)

    def __len__(self) -> int:
        return len(self._live)

    def __contains__(self, cell: Cell) -> bool:
        return cell in self._live

    def __iter__(self) -> Iterator[Cell]:
        return iter(self._live)

    def __eq__(self, other: object) -> bool:
        if isinstance(other, Board):
            return self._live == other._live
        return NotImplemented

    @staticmethod
    def _neighbors(cell: Cell) -> Iterator[Cell]:
        x, y = cell
        for dx in (-1, 0, 1):
            for dy in (-1, 0, 1):
                if dx or dy:
                    yield (x + dx, y + dy)

    def step(self) -> "Board":
        """Return a new board advanced by one generation."""
        neighbor_counts: dict[Cell, int] = {}
        for cell in self._live:
            for neighbor in self._neighbors(cell):
                neighbor_counts[neighbor] = neighbor_counts.get(neighbor, 0) + 1

        next_live = {
            cell
            for cell, count in neighbor_counts.items()
            if count == 3 or (count == 2 and cell in self._live)
        }
        return Board(next_live)

    def bounds(self) -> tuple[int, int, int, int]:
        """Return (min_x, min_y, max_x, max_y) covering all live cells.

        Raises ``ValueError`` if the board is empty.
        """
        if not self._live:
            raise ValueError("cannot compute bounds of an empty board")
        xs = [x for x, _ in self._live]
        ys = [y for _, y in self._live]
        return min(xs), min(ys), max(xs), max(ys)

    def render(self, alive: str = "#", dead: str = ".", padding: int = 1) -> str:
        """Render the live region of the board as a string grid."""
        if not self._live:
            return ""
        min_x, min_y, max_x, max_y = self.bounds()
        min_x -= padding
        min_y -= padding
        max_x += padding
        max_y += padding
        rows = []
        for y in range(min_y, max_y + 1):
            row = "".join(
                alive if (x, y) in self._live else dead
                for x in range(min_x, max_x + 1)
            )
            rows.append(row)
        return "\n".join(rows)
