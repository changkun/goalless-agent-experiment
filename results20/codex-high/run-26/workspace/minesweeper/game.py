"""Core Minesweeper game logic (no UI dependencies)."""

from __future__ import annotations

import random


class GameOver(Exception):
    """Raised when a mine is revealed."""


class GameWon(Exception):
    """Raised when all safe cells are revealed."""


class Cell:
    __slots__ = ("mine", "revealed", "flagged", "neighbors")

    def __init__(self, mine: bool = False):
        self.mine = mine
        self.revealed = False
        self.flagged = False
        self.neighbors = 0


class Board:
    def __init__(self, rows: int, cols: int, mines: int, rng: random.Random | None = None):
        if rows <= 0 or cols <= 0:
            raise ValueError("board dimensions must be positive")
        if mines < 0 or mines > rows * cols:
            raise ValueError("mine count out of range")
        self.rows = rows
        self.cols = cols
        self.mines = mines
        self.rng = rng or random.Random()
        self.cells = [[Cell() for _ in range(cols)] for _ in range(rows)]
        self.revealed_count = 0
        self._place_mines()
        self._count_neighbors()

    def _place_mines(self) -> None:
        positions = self.rng.sample(range(self.rows * self.cols), self.mines)
        for p in positions:
            r, c = divmod(p, self.cols)
            self.cells[r][c].mine = True

    def _count_neighbors(self) -> None:
        for r in range(self.rows):
            for c in range(self.cols):
                self.cells[r][c].neighbors = sum(
                    1
                    for dr, dc in self._neighbor_offsets(r, c)
                    if self.cells[r + dr][c + dc].mine
                )

    def _neighbor_offsets(self, r: int, c: int):
        for dr in (-1, 0, 1):
            for dc in (-1, 0, 1):
                if dr == 0 and dc == 0:
                    continue
                nr, nc = r + dr, c + dc
                if 0 <= nr < self.rows and 0 <= nc < self.cols:
                    yield dr, dc

    def in_bounds(self, r: int, c: int) -> bool:
        return 0 <= r < self.rows and 0 <= c < self.cols

    def toggle_flag(self, r: int, c: int) -> None:
        cell = self.cells[r][c]
        if cell.revealed:
            return
        cell.flagged = not cell.flagged

    def reveal(self, r: int, c: int) -> None:
        if not self.in_bounds(r, c):
            raise IndexError("cell out of bounds")
        cell = self.cells[r][c]
        if cell.revealed or cell.flagged:
            return
        cell.revealed = True
        self.revealed_count += 1

        if cell.mine:
            raise GameOver(f"hit a mine at ({r}, {c})")

        if cell.neighbors == 0:
            for dr, dc in self._neighbor_offsets(r, c):
                n = self.cells[r + dr][c + dc]
                if not n.revealed and not n.mine and not n.flagged:
                    self.reveal(r + dr, c + dc)

        if self.solved():
            raise GameWon()

    def solved(self) -> bool:
        return self.revealed_count == self.rows * self.cols - self.mines
