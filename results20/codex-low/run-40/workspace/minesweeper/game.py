"""Core Minesweeper game engine."""

from __future__ import annotations

import random
from dataclasses import dataclass, field


class CellState:
    HIDDEN = "hidden"
    REVEALED = "revealed"
    FLAGGED = "flagged"


@dataclass
class Board:
    """A rectangular Minesweeper board.

    Attributes:
        rows: Number of rows.
        cols: Number of columns.
        mines: Number of mines to place.
        mines_positions: Set of (row, col) coordinates containing mines.
        state: 2D list of CellState values.
        counts: 2D list of adjacent-mine counts for each cell.
        first_move: Whether the first reveal is still pending.
    """

    rows: int
    cols: int
    mines: int
    rng: random.Random = field(default_factory=random.Random)
    mines_positions: set[tuple[int, int]] = field(default_factory=set)
    state: list[list[str]] = field(init=False)
    counts: list[list[int]] = field(init=False)
    first_move: bool = True
    revealed: int = 0
    flagged: int = 0

    def __post_init__(self) -> None:
        if self.rows < 1 or self.cols < 1:
            raise ValueError("Board dimensions must be positive.")
        if self.mines < 0 or self.mines > self.rows * self.cols:
            raise ValueError("Number of mines is out of range.")
        self.state = [
            [CellState.HIDDEN for _ in range(self.cols)] for _ in range(self.rows)
        ]
        self.counts = [[0 for _ in range(self.cols)] for _ in range(self.rows)]

    @property
    def safe_cells(self) -> int:
        """Number of non-mine cells."""
        return self.rows * self.cols - self.mines

    @property
    def won(self) -> bool:
        """Whether all safe cells have been revealed."""
        return self.revealed == self.safe_cells

    def _neighbors(self, row: int, col: int) -> list[tuple[int, int]]:
        neighbors: list[tuple[int, int]] = []
        for dr in (-1, 0, 1):
            for dc in (-1, 0, 1):
                if dr == 0 and dc == 0:
                    continue
                nr, nc = row + dr, col + dc
                if 0 <= nr < self.rows and 0 <= nc < self.cols:
                    neighbors.append((nr, nc))
        return neighbors

    def _place_mines(self, clear: tuple[int, int]) -> None:
        """Randomly place mines, avoiding the cells around `clear` (inclusive)."""
        excluded = set(self._neighbors(*clear)) | {clear}
        candidates = [
            (r, c)
            for r in range(self.rows)
            for c in range(self.cols)
            if (r, c) not in excluded
        ]
        if len(candidates) < self.mines:
            # Fallback: not enough cells outside the exclusion zone, so relax it.
            candidates = [
                (r, c)
                for r in range(self.rows)
                for c in range(self.cols)
                if (r, c) != clear
            ]
            if len(candidates) < self.mines:
                raise ValueError("Not enough cells to place mines safely.")
        self.mines_positions = set(self.rng.sample(candidates, self.mines))
        for (r, c) in self.mines_positions:
            for (nr, nc) in self._neighbors(r, c):
                self.counts[nr][nc] += 1
        self.first_move = False

    def flag(self, row: int, col: int) -> None:
        """Toggle a flag on a hidden cell."""
        self._check_bounds(row, col)
        cell = self.state[row][col]
        if cell == CellState.HIDDEN:
            self.state[row][col] = CellState.FLAGGED
            self.flagged += 1
        elif cell == CellState.FLAGGED:
            self.state[row][col] = CellState.HIDDEN
            self.flagged -= 1

    def reveal(self, row: int, col: int) -> bool:
        """Reveal a cell. Returns True if it was a mine (game lost).

        The first reveal is guaranteed safe and triggers mine placement,
        so the opening move can never be a losing one.
        """
        self._check_bounds(row, col)
        if self.state[row][col] != CellState.HIDDEN:
            return False

        if self.first_move:
            self._place_mines((row, col))

        cell_is_mine = (row, col) in self.mines_positions
        if cell_is_mine:
            self.state[row][col] = CellState.REVEALED
            return True

        self._reveal_region(row, col)
        return False

    def _reveal_region(self, row: int, col: int) -> None:
        """Flood-fill reveal of adjacent zero-count cells."""
        stack = [(row, col)]
        while stack:
            r, c = stack.pop()
            if not self._in_bounds(r, c):
                continue
            if self.state[r][c] != CellState.HIDDEN:
                continue
            self.state[r][c] = CellState.REVEALED
            self.revealed += 1
            if self.counts[r][c] == 0:
                for neighbor in self._neighbors(r, c):
                    if self.state[neighbor[0]][neighbor[1]] == CellState.HIDDEN:
                        stack.append(neighbor)

    def _check_bounds(self, row: int, col: int) -> None:
        if not self._in_bounds(row, col):
            raise IndexError(f"Cell ({row}, {col}) is out of bounds.")

    def _in_bounds(self, row: int, col: int) -> bool:
        return 0 <= row < self.rows and 0 <= col < self.cols
