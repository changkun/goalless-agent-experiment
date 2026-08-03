"""Pure 2048 game logic (no I/O), so it can be tested independently."""

from __future__ import annotations

import random
from dataclasses import dataclass
from enum import Enum


class Direction(Enum):
    UP = "up"
    DOWN = "down"
    LEFT = "left"
    RIGHT = "right"


@dataclass
class MoveResult:
    moved: bool
    score_gained: int
    spawned: bool


def _compress(line: list[int]) -> list[int]:
    """Slide non-zero cells to the left, returning a new list."""
    return [v for v in line if v != 0] + [0] * (line.count(0))


def _merge(line: list[int]) -> tuple[list[int], int]:
    """Merge adjacent equal tiles leftward. Returns (line, score)."""
    compressed = _compress(line)
    score = 0
    out: list[int] = []
    i = 0
    n = len(compressed)
    while i < n:
        if i + 1 < n and compressed[i] == compressed[i + 1]:
            merged = compressed[i] * 2
            out.append(merged)
            score += merged
            i += 2
        else:
            out.append(compressed[i])
            i += 1
    out += [0] * (n - len(out))
    return out, score


class Board:
    """A square 2048 board of ``size`` x ``size``."""

    def __init__(self, size: int = 4, rng: random.Random | None = None) -> None:
        if size < 2:
            raise ValueError("board size must be >= 2")
        self.size = size
        self.grid: list[list[int]] = [[0] * size for _ in range(size)]
        self.score = 0
        self._rng = rng or random.Random()
        self.spawn_tile()
        self.spawn_tile()

    def _empty_cells(self) -> list[tuple[int, int]]:
        return [
            (r, c)
            for r in range(self.size)
            for c in range(self.size)
            if self.grid[r][c] == 0
        ]

    def spawn_tile(self) -> bool:
        """Place a 2 (90%) or 4 (10%) in a random empty cell."""
        empty = self._empty_cells()
        if not empty:
            return False
        r, c = self._rng.choice(empty)
        self.grid[r][c] = 2 if self._rng.random() < 0.9 else 4
        return True

    def _slide(self, direction: Direction) -> tuple[bool, int]:
        """Slide and merge the board in a direction. Returns (moved, score)."""
        moved = False
        total_score = 0
        for row in range(self.size):
            if direction in (Direction.LEFT, Direction.RIGHT):
                line = [self.grid[row][c] for c in range(self.size)]
            else:
                line = [self.grid[r][row] for r in range(self.size)]
            merged, score = _merge_reversed(line) if direction in (Direction.RIGHT, Direction.DOWN) else _merge(line)
            total_score += score
            if merged != line:
                moved = True
            for col in range(self.size):
                if direction in (Direction.LEFT, Direction.RIGHT):
                    self.grid[row][col] = merged[col]
                else:
                    self.grid[col][row] = merged[col]
        return moved, total_score

    def move(self, direction: Direction) -> MoveResult:
        """Apply a move. Spawns a new tile only if the board changed."""
        moved, gained = self._slide(direction)
        spawned = False
        if moved:
            self.score += gained
            spawned = self.spawn_tile()
        return MoveResult(moved=moved, score_gained=gained, spawned=spawned)

    def can_move(self) -> bool:
        """True if any move is possible (empty cell or adjacent equal tiles)."""
        if self._empty_cells():
            return True
        for r in range(self.size):
            for c in range(self.size):
                value = self.grid[r][c]
                if r + 1 < self.size and self.grid[r + 1][c] == value:
                    return True
                if c + 1 < self.size and self.grid[r][c + 1] == value:
                    return True
        return False

    def max_tile(self) -> int:
        return max(max(row) for row in self.grid)

    def is_won(self, target: int = 2048) -> bool:
        return self.max_tile() >= target


def _merge_reversed(line: list[int]) -> tuple[list[int], int]:
    """Merge a line moving right/down by reversing, merging, then reversing back."""
    merged, score = _merge(list(reversed(line)))
    return list(reversed(merged)), score
