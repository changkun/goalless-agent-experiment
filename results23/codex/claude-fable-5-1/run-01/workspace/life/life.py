"""Conway's Game of Life on an infinite plane, using a sparse set of live cells."""

from __future__ import annotations

from collections import Counter
from typing import FrozenSet, Iterable, Tuple

Cell = Tuple[int, int]
Board = FrozenSet[Cell]

NEIGHBOR_OFFSETS = [
    (dx, dy) for dx in (-1, 0, 1) for dy in (-1, 0, 1) if (dx, dy) != (0, 0)
]


def step(board: Board) -> Board:
    """Advance the board one generation."""
    counts = Counter(
        (x + dx, y + dy) for (x, y) in board for (dx, dy) in NEIGHBOR_OFFSETS
    )
    return frozenset(
        cell
        for cell, count in counts.items()
        if count == 3 or (count == 2 and cell in board)
    )


def parse(pattern: str, origin: Cell = (0, 0)) -> Board:
    """Parse a plaintext pattern where '#' or 'O' marks a live cell."""
    ox, oy = origin
    return frozenset(
        (ox + x, oy + y)
        for y, line in enumerate(pattern.strip("\n").splitlines())
        for x, char in enumerate(line)
        if char in "#O"
    )


def render(board: Iterable[Cell], width: int, height: int, origin: Cell = (0, 0)) -> str:
    """Render a viewport of the board as text."""
    ox, oy = origin
    live = set(board)
    rows = []
    for y in range(oy, oy + height):
        rows.append(
            "".join("█" if (x, y) in live else "·" for x in range(ox, ox + width))
        )
    return "\n".join(rows)


PATTERNS = {
    "glider": """
.#.
..#
###
""",
    "blinker": "###",
    "r-pentomino": """
.##
##.
.#.
""",
    "gosper-gun": """
........................#...........
......................#.#...........
............##......##............##
...........#...#....##............##
##........#.....#...##..............
##........#...#.##....#.#...........
..........#.....#.......#...........
...........#...#....................
............##......................
""",
}
