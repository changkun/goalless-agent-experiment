"""A dependency-free 2048 game engine.

The board is a flat list of ``size * size`` integers, row-major. Empty
cells are represented by ``0``; every other cell holds a power of two.
"""

from __future__ import annotations

import random
from dataclasses import dataclass
from enum import Enum
from typing import List, Optional, Sequence, Tuple

STARTING_TILES = 2


class Move(Enum):
    """Valid player moves."""

    UP = "up"
    DOWN = "down"
    LEFT = "left"
    RIGHT = "right"


@dataclass(frozen=True)
class GameResult:
    """Outcome of one move."""

    moved: bool
    gained: int
    game_over: bool
    won: bool
    board: Tuple[int, ...]


class Game:
    """A 2048 game with a deterministic, testable core.

    Pass a fixed ``seed`` (or inject tiles via :meth:`set_tiles`) to make
    moves reproducible in tests.
    """

    def __init__(
        self,
        size: int = 4,
        start_tiles: int = STARTING_TILES,
        seed: Optional[int] = None,
        win_tile: int = 2048,
    ) -> None:
        if size < 2:
            raise ValueError("size must be at least 2")
        if start_tiles < 1:
            raise ValueError("start_tiles must be at least 1")
        if start_tiles > size * size:
            raise ValueError("start_tiles cannot exceed the board size")
        self.size = size
        self.start_tiles = start_tiles
        self.win_tile = win_tile
        self._rng = random.Random(seed)
        self.board = [0] * (size * size)
        self.score = 0
        self.won = False
        self.moves = 0
        for _ in range(start_tiles):
            self._spawn_tile()

    # -- public API ----------------------------------------------------

    def set_tiles(self, tiles: Sequence[int]) -> None:
        """Replace the board and reset score/won/moves (for tests)."""
        values = list(tiles)
        if len(values) != self.size * self.size:
            raise ValueError(
                f"expected {self.size * self.size} tiles, got {len(values)}"
            )
        if any(v < 0 for v in values):
            raise ValueError("tile values must be non-negative")
        self.board = values
        self.score = 0
        self.won = False
        self.moves = 0

    def move(self, move: Move) -> GameResult:
        """Apply one move, spawn a tile when the board changes, and report."""
        board, gained = self._slide(list(self.board), move)
        moved = board != self.board
        if moved:
            self.board = board
            self.score += gained
            self.moves += 1
            if not self.won and any(t >= self.win_tile for t in self.board):
                self.won = True
            self._spawn_tile()
        return GameResult(
            moved=moved,
            gained=gained,
            game_over=self.is_game_over(),
            won=self.won,
            board=tuple(self.board),
        )

    def is_game_over(self) -> bool:
        """True when no move can change the board."""
        if any(t == 0 for t in self.board):
            return False
        for move in Move:
            slid, _ = self._slide(list(self.board), move)
            if slid != self.board:
                return False
        return True

    def empty_cells(self) -> List[int]:
        """Indices of cells currently holding zero."""
        return [i for i, t in enumerate(self.board) if t == 0]

    # -- helpers -------------------------------------------------------

    def _slide(self, board: List[int], move: Move) -> Tuple[List[int], int]:
        """Compress and merge tiles in ``move``'s direction.

        Tiles are read as a set of "lines" — for LEFT/RIGHT each row, for
        UP/DOWN each column — ordered so that index ``0`` is the leading edge
        toward which tiles slide. Each line is merged once and written back.
        """
        lines = self._lines_for(move)
        result = list(board)
        gained = 0
        for indices in lines:
            values = [result[i] for i in indices]
            merged, line_gain = self._merge_values(values)
            gained += line_gain
            for i, value in zip(indices, merged):
                result[i] = value
        return result, gained

    def _lines_for(self, move: Move) -> List[List[int]]:
        """Indices of each line (row or column) in merge order."""
        size = self.size
        n = size * size
        if move == Move.LEFT:
            return [
                [r * size + c for c in range(size)] for r in range(size)
            ]
        if move == Move.RIGHT:
            return [
                [r * size + c for c in reversed(range(size))] for r in range(size)
            ]
        if move == Move.UP:
            return [
                [c + r * size for r in range(size)] for c in range(size)
            ]
        # DOWN: columns ordered bottom-first so tiles slide toward the bottom.
        return [
            [c + r * size for r in reversed(range(size))] for c in range(size)
        ]

    def _merge_values(self, values: Sequence[int]) -> Tuple[List[int], int]:
        """Merge a single line once: compress, combine equal neighbours."""
        tiles = [t for t in values if t != 0]
        merged: List[int] = []
        gained = 0
        i = 0
        while i < len(tiles):
            if i + 1 < len(tiles) and tiles[i] == tiles[i + 1]:
                value = tiles[i] * 2
                merged.append(value)
                gained += value
                i += 2
            else:
                merged.append(tiles[i])
                i += 1
        merged += [0] * (len(values) - len(merged))
        return merged, gained

    def _spawn_tile(self) -> None:
        """Add a 2 (90%) or 4 (10%) tile to a random empty cell."""
        empty = self.empty_cells()
        if not empty:
            return
        index = self._rng.choice(empty)
        self.board[index] = self._rng.choice([2, 2, 2, 2, 2, 2, 2, 2, 2, 4])

    @staticmethod
    def _transpose(board: List[int]) -> List[int]:
        size = int(len(board) ** 0.5)
        return [
            board[row * size + col]
            for col in range(size)
            for row in range(size)
        ]

    @staticmethod
    def _flip(board: List[int]) -> List[int]:
        size = int(len(board) ** 0.5)
        flipped = []
        for start in range(0, len(board), size):
            flipped.extend(reversed(board[start : start + size]))
        return flipped
