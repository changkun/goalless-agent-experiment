"""Pure 2048 game logic.

This module has no I/O or UI dependencies so it can be tested and reused
independently.  A board is a ``list`` of ``list`` of ``int``; 0 means empty.
"""

from __future__ import annotations

import random
from typing import Callable, Iterable, List, Optional, Sequence, Tuple

EMPTY = 0
WIN_TILE = 2048

# Directions. The +/- refer to the axis and the direction of movement,
# matching how a 2D index grows.
Direction = Tuple[int, int]  # (delta_i, delta_j)
LEFT: Direction = (0, -1)
RIGHT: Direction = (0, 1)
UP: Direction = (-1, 0)
DOWN: Direction = (1, 0)

AllDirection = Iterable[Direction]
_RandGen = Callable[..., Optional[int]]


def blank_board(size: int = 4) -> List[List[int]]:
    """Return a ``size`` x ``size`` board filled with empty cells."""
    return [[EMPTY for _ in range(size)] for _ in range(size)]


def _empty_cells(board: List[List[int]]) -> List[Tuple[int, int]]:
    return [
        (i, j)
        for i, row in enumerate(board)
        for j, value in enumerate(row)
        if value == EMPTY
    ]


def add_random_tile(
    board: List[List[int]],
    rng: _RandGen = random.randint,
    spawn_values: Sequence[int] = (2, 4),
) -> Tuple[int, int]:
    """Place a random tile in an empty cell and return its coordinates.

    ``rng`` must be a callable accepting ``(a, b)`` and returning an int; a
    smaller value is more likely (default 90% for 2, 10% for 4) when
    ``spawn_values`` is the default.
    """
    cells = _empty_cells(board)
    if not cells:
        raise ValueError("board is full")
    i, j = cells[rng(0, len(cells) - 1)]
    value = spawn_values[1] if rng(0, 9) == 9 else spawn_values[0]
    board[i][j] = value
    return i, j


def _slide_row(row: List[int]) -> Tuple[List[int], int]:
    """Slide one row leftward, merging equal neighbours. Returns new row and score gained."""
    compact = [v for v in row if v != EMPTY]
    merged: List[int] = []
    score = 0
    k = 0
    while k < len(compact):
        if k + 1 < len(compact) and compact[k] == compact[k + 1]:
            value = compact[k] * 2
            merged.append(value)
            score += value
            k += 2
        else:
            merged.append(compact[k])
            k += 1
    merged.extend([EMPTY] * (len(row) - len(merged)))
    return merged, score


def _move_line(indices: Sequence[Tuple[int, int]], board: List[List[int]]) -> Tuple[int, bool]:
    """Read the cells along ``indices``, slide them toward the first index, write back."""
    line = [board[i][j] for i, j in indices]
    slid, score = _slide_row(line)
    changed = any(a != b for a, b in zip(line, slid))
    for (i, j), value in zip(indices, slid):
        board[i][j] = value
    return score, changed


def move(board: List[List[int]], direction: Direction) -> Tuple[List[List[int]], int, bool]:
    """Move ``board`` in ``direction`` in place.

    Returns ``(board, score_gained, moved)`` where ``moved`` is True if any
    tile moved or merged. ``board`` is mutated directly.
    """
    size = len(board)
    if direction == LEFT:
        lines = [[(i, j) for j in range(size)] for i in range(size)]
    elif direction == RIGHT:
        lines = [[(i, j) for j in range(size - 1, -1, -1)] for i in range(size)]
    elif direction == UP:
        lines = [[(i, j) for i in range(size)] for j in range(size)]
    elif direction == DOWN:
        lines = [[(i, j) for i in range(size - 1, -1, -1)] for j in range(size)]
    else:
        raise ValueError(f"unknown direction: {direction}")

    total_score = 0
    any_changed = False
    for line in lines:
        score, changed = _move_line(line, board)
        total_score += score
        any_changed = any_changed or changed
    return board, total_score, any_changed


def has_won(board: List[List[int]], target: int = WIN_TILE) -> bool:
    """True if any cell reached the target tile."""
    return any(v == target for row in board for v in row)


def can_move(board: List[List[int]]) -> bool:
    """True if at least one move is still possible."""
    size = len(board)
    if any(v == EMPTY for row in board for v in row):
        return True
    for i in range(size):
        for j in range(size):
            value = board[i][j]
            if i + 1 < size and board[i + 1][j] == value:
                return True
            if j + 1 < size and board[i][j + 1] == value:
                return True
    return False
