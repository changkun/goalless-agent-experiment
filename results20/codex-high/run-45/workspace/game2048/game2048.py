"""Core logic for the 2048 puzzle game.

The board is a square N x N grid of tiles whose values are powers of two
(or zero, meaning empty). The rules are the classic 2048 rules:

* A move slides all tiles in a direction, merging equal adjacent tiles once.
* After each successful move, a new tile (2, or rarely 4) is spawned.
* The game is won when a tile reaches ``2048`` and lost when no moves remain.
"""

from __future__ import annotations

import random
from dataclasses import dataclass, field
from typing import Callable, Iterator, List, Sequence, Tuple

WINNING_TILE = 2048
_NEW_TILE_VALUES = (2, 2, 2, 4)  # 75% chance of 2, 25% chance of 4.

Board = List[List[int]]


def empty_board(size: int) -> Board:
    """Return a ``size`` x ``size`` board filled with zeros."""
    return [[0 for _ in range(size)] for _ in range(size)]


def _tiles(board: Board) -> Iterator[Tuple[int, int, int]]:
    """Yield ``(row, col, value)`` for every cell, row-major."""
    for r, row in enumerate(board):
        for c, value in enumerate(row):
            yield r, c, value


def _transpose(board: Board) -> Board:
    """Return the transposed board (rows and columns swapped)."""
    return [list(row) for row in zip(*board)]


def _reverse_rows(board: Board) -> Board:
    """Return a board with every row reversed."""
    return [list(reversed(row)) for row in board]


def _line_move(line: Sequence[int]) -> Tuple[List[int], int]:
    """Slide and merge a single row towards the start (index 0).

    Returns the resulting row and the score gained from merges. Zeroes are
    removed (tiles slide towards the start) and adjacent equal tiles merge
    once, doubling the survivor.
    """
    moved = [value for value in line if value != 0]
    merged: List[int] = []
    score = 0
    i = 0
    while i < len(moved):
        if i + 1 < len(moved) and moved[i] == moved[i + 1]:
            value = moved[i] * 2
            merged.append(value)
            score += value
            i += 2
        else:
            merged.append(moved[i])
            i += 1
    return merged + [0] * (len(line) - len(merged)), score


def _transform_for(direction: str, board: Board) -> Tuple[Board, Callable[[Board], Board]]:
    """Normalise a board so a move can always be handled as a leftward move.

    Returns the board to operate on and a transform to convert the result
    back to the original orientation.
    """
    size = len(board)
    if direction == "left":
        return board, lambda m: m
    if direction == "right":
        return _reverse_rows(board), lambda m: _reverse_rows(m)
    if direction == "up":
        return _transpose(board), lambda m: _transpose(m)
    if direction == "down":
        return _reverse_rows(_transpose(board)), lambda m: _transpose(_reverse_rows(m))
    raise ValueError(f"unknown direction: {direction!r}")


def move(board: Board, direction: str) -> Tuple[Board, bool, int]:
    """Move the board in ``direction``.

    Returns ``(new_board, changed, score)`` where ``changed`` is True when at
    least one tile moved or merged, and ``score`` is the points gained from
    merges during this move.

    Note: :func:`move` only slides and merges; it does not spawn new tiles.
    Spawning is left to :func:`spawn_tile` / :func:`move_and_spawn`.
    """
    normalised, restore = _transform_for(direction, board)

    new_rows: List[List[int]] = []
    total_score = 0
    for row in normalised:
        new_line, score = _line_move(row)
        new_rows.append(new_line)
        total_score += score

    restored = restore(new_rows)
    changed = restored != board
    return restored, changed, total_score


def move_and_spawn(board: Board, direction: str, rng: random.Random) -> Tuple[Board, bool, int]:
    """Slide/merge (via :func:`move`); if anything changed, spawn a tile."""
    new_board, changed, score = move(board, direction)
    if changed:
        spawn_tile(new_board, rng)
    return new_board, changed, score


def spawn_tile(board: Board, rng: random.Random) -> bool:
    """Add a random new tile (2 or 4) to a random empty cell.

    Returns True if a tile was spawned, False if the board was full.
    """
    empty = [(r, c) for r, c, value in _tiles(board) if value == 0]
    if not empty:
        return False
    r, c = rng.choice(empty)
    board[r][c] = rng.choice(_NEW_TILE_VALUES)
    return True


def available_moves(board: Board) -> List[str]:
    """Return the directions that would change the board (legal moves)."""
    legal: List[str] = []
    for direction in ("left", "right", "up", "down"):
        _, changed, _ = move(board, direction)
        if changed:
            legal.append(direction)
    return legal


def is_game_over(board: Board) -> bool:
    """Return True when no move can change the board (and thus the game ends)."""
    return not available_moves(board)


def has_won(board: Board) -> bool:
    """Return True when any tile has reached ``WINNING_TILE``."""
    return any(value == WINNING_TILE for _, _, value in _tiles(board))


@dataclass
class Game:
    """A playable 2048 game instance."""

    size: int = 4
    seed: int | None = None
    board: Board = field(init=False)
    score: int = field(default=0, init=False)
    _rng: random.Random = field(init=False, repr=False)

    def __post_init__(self) -> None:
        self.board = empty_board(self.size)
        self._rng = random.Random(self.seed)
        spawn_tile(self.board, self._rng)
        spawn_tile(self.board, self._rng)

    def play(self, direction: str) -> bool:
        """Apply a move. Returns True if the board changed."""
        new_board, changed, score = move(self.board, direction)
        if not changed:
            return False
        self.score += score
        self.board = new_board
        spawn_tile(self.board, self._rng)
        return True

    @property
    def over(self) -> bool:
        return is_game_over(self.board)

    @property
    def won(self) -> bool:
        return has_won(self.board)
