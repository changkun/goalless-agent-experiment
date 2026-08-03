"""Core Minesweeper game logic, free of any I/O concerns."""

from __future__ import annotations

import random
from dataclasses import dataclass, field


@dataclass
class Cell:
    """A single board cell."""

    mine: bool = False
    revealed: bool = False
    flagged: bool = False
    adjacent: int = 0


class Game:
    """A single game of Minesweeper."""

    WIDTH = 9
    HEIGHT = 9
    MINES = 10

    def __init__(self, width: int = WIDTH, height: int = HEIGHT, mines: int = MINES,
                 rng: random.Random | None = None) -> None:
        if mines >= width * height:
            raise ValueError("number of mines must be less than the cell count")
        self.width = width
        self.height = height
        self.mines = mines
        self._rng = rng or random.Random()
        self.cells: list[Cell] = [Cell() for _ in range(width * height)]
        self.lost = False
        self.won = False
        self._placed = False

    # -- indexing helpers ------------------------------------------------
    def index(self, x: int, y: int) -> int:
        return y * self.width + x

    def in_bounds(self, x: int, y: int) -> bool:
        return 0 <= x < self.width and 0 <= y < self.height

    def neighbors(self, x: int, y: int):
        for dy in (-1, 0, 1):
            for dx in (-1, 0, 1):
                if dx == 0 and dy == 0:
                    continue
                nx, ny = x + dx, y + dy
                if self.in_bounds(nx, ny):
                    yield nx, ny

    # -- setup -----------------------------------------------------------
    def _place_mines(self, safe: tuple[int, int] | None = None) -> None:
        """Randomly place mines, guaranteeing ``safe`` is never a mine."""
        cells = [i for i in range(len(self.cells))]
        if safe is not None:
            cells.remove(self.index(*safe))
            for nx, ny in self.neighbors(*safe):
                i = self.index(nx, ny)
                if i in cells:
                    cells.remove(i)
        for i in self._rng.sample(cells, self.mines):
            self.cells[i].mine = True
        for x in range(self.width):
            for y in range(self.height):
                cell = self.cells[self.index(x, y)]
                cell.adjacent = sum(
                    1 for nx, ny in self.neighbors(x, y)
                    if self.cells[self.index(nx, ny)].mine
                )
        self._placed = True

    # -- actions ---------------------------------------------------------
    def reveal(self, x: int, y: int) -> None:
        if not self._placed:
            self._place_mines((x, y))
        i = self.index(x, y)
        cell = self.cells[i]
        if cell.revealed or cell.flagged or self.lost or self.won:
            return
        cell.revealed = True
        if cell.mine:
            self.lost = True
            return
        if cell.adjacent == 0:
            self._flood(x, y)
        self._check_victory()

    def toggle_flag(self, x: int, y: int) -> None:
        if self.lost or self.won:
            return
        if not self._placed:
            self._place_mines()
        cell = self.cells[self.index(x, y)]
        if not cell.revealed:
            cell.flagged = not cell.flagged

    def _flood(self, x: int, y: int) -> None:
        """Reveal all contiguous empty cells (BFS flood fill)."""
        stack = [(x, y)]
        while stack:
            cx, cy = stack.pop()
            for nx, ny in self.neighbors(cx, cy):
                cell = self.cells[self.index(nx, ny)]
                if cell.revealed or cell.flagged or cell.mine:
                    continue
                cell.revealed = True
                if cell.adjacent == 0:
                    stack.append((nx, ny))

    def _check_victory(self) -> None:
        if self.lost:
            return
        revealed = sum(1 for c in self.cells if c.revealed)
        if revealed == len(self.cells) - self.mines:
            self.won = True

    # -- state -----------------------------------------------------------
    def flags_remaining(self) -> int:
        flagged = sum(1 for c in self.cells if c.flagged)
        return self.mines - flagged

    def is_mine(self, x: int, y: int) -> bool:
        return self.cells[self.index(x, y)].mine
