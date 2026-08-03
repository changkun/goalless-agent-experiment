"""Conway's Game of Life.

A faithful implementation of John Conway's cellular automaton:
  * A live cell with 2 or 3 live neighbours survives.
  * A dead cell with exactly 3 live neighbours becomes alive.
  * Everything else dies or stays dead.

The core logic lives in `Grid`, a fully-implemented, fast, and testable
class that is independent of any display or CLI concerns. The `live` and
`lif` modules add the terminal front-end on top.
"""

from __future__ import annotations

from itertools import product

# Offsets to the eight neighbouring cells of any given cell.
_NEIGHBOUR_OFFSETS = tuple(
    (dr, dc)
    for dr, dc in product((-1, 0, 1), repeat=2)
    if (dr, dc) != (0, 0)
)


class Grid:
    """A bounded grid of cells on which the Game of Life evolves.

    Cells are stored in a dense 2-D list of booleans (`True` = alive).
    The grid has fixed dimensions; cells outside the boundary are treated
    as permanently dead.
    """

    __slots__ = ("rows", "cols", "_cells")

    def __init__(self, rows: int, cols: int) -> None:
        if rows <= 0 or cols <= 0:
            raise ValueError("grid dimensions must be positive")
        self.rows = rows
        self.cols = cols
        self._cells = [[False] * cols for _ in range(rows)]

    @classmethod
    def from_rows(cls, rows: list[str]) -> "Grid":
        """Build a grid from a list of strings where `#` (or any non-space,
        non-`.` char) marks a live cell.

        Example:
            Grid.from_rows([".##", "#.#", ".#."])
        """
        height = len(rows)
        width = max(len(r) for r in rows) if rows else 0
        grid = cls(height, width)
        for r, row in enumerate(rows):
            for c, ch in enumerate(row):
                if ch not in " .":
                    grid.set(r, c, True)
        return grid

    def get(self, row: int, col: int) -> bool:
        """Return whether the cell at (row, col) is alive.

        Out-of-bounds coordinates read as dead.
        """
        if 0 <= row < self.rows and 0 <= col < self.cols:
            return self._cells[row][col]
        return False

    def set(self, row: int, col: int, alive: bool) -> None:
        """Set the cell at (row, col) to a live/dead state. Does nothing if
        the coordinate is out of bounds."""
        if 0 <= row < self.rows and 0 <= col < self.cols:
            self._cells[row][col] = alive

    def toggle(self, row: int, col: int) -> None:
        """Flip the state of a single cell."""
        if 0 <= row < self.rows and 0 <= col < self.cols:
            self._cells[row][col] = not self._cells[row][col]

    def alive_count(self) -> int:
        """Return the total number of live cells."""
        return sum(sum(row) for row in self._cells)

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Grid):
            return NotImplemented
        return (
            self.rows == other.rows
            and self.cols == other.cols
            and self._cells == other._cells
        )

    def __repr__(self) -> str:
        return f"Grid({self.rows}x{self.cols}, {self.alive_count()} alive)"

    def _neighbours(self, row: int, col: int) -> int:
        """Count live neighbours around (row, col), clipping at the edge."""
        if not (0 <= row < self.rows and 0 <= col < self.cols):
            raise IndexError(
                f"({row}, {col}) is outside the {self.rows}x{self.cols} grid"
            )
        live = 0
        cells = self._cells
        rows, cols = self.rows, self.cols
        for dr, dc in _NEIGHBOUR_OFFSETS:
            nr, nc = row + dr, col + dc
            if 0 <= nr < rows and 0 <= nc < cols and cells[nr][nc]:
                live += 1
                if live > 3:  # Short-circuit: never need more than 4.
                    return live
        return live

    def step(self) -> None:
        """Advance the grid by one generation in place."""
        rows, cols = self.rows, self.cols
        cells = self._cells
        next_cells = [[False] * cols for _ in range(rows)]
        for r in range(rows):
            row = cells[r]
            next_row = next_cells[r]
            for c in range(cols):
                n = self._neighbours(r, c)
                if row[c]:
                    # Survival: a live cell lives on with 2 or 3 neighbours.
                    next_row[c] = n in (2, 3)
                else:
                    # Birth: a dead cell springs to life with exactly 3.
                    next_row[c] = n == 3
        self._cells = next_cells

    def render(self, alive: str = "#", dead: str = " ") -> str:
        """Render the grid as a string, one line per row."""
        return "\n".join(
            "".join(alive if cell else dead for cell in row)
            for row in self._cells
        )
