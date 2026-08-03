"""Game of Life board as a set of live cells.

A board is represented as a `set[tuple[int, int]]` of live cell coordinates.
All rules live here so they can be tested independently of the CLI.
"""

from __future__ import annotations

LIVE, DEAD = "#", "."

NEIGHBOR_DELTAS = [
    (-1, -1), (-1, 0), (-1, 1),
    (0, -1), (0, 1),
    (1, -1), (1, 0), (1, 1),
]


def neighbors(cell: tuple[int, int]) -> set[tuple[int, int]]:
    """Return the 8 cells surrounding ``cell``."""
    x, y = cell
    return {(x + dx, y + dy) for dx, dy in NEIGHBOR_DELTAS}


def tick(cells: set[tuple[int, int]]) -> set[tuple[int, int]]:
    """Advance the board one generation using Conway's rules.

    - A live cell survives with 2 or 3 live neighbors.
    - A dead cell becomes live with exactly 3 live neighbors.
    """
    # Any cell that can possibly change is a live cell or one of its neighbors.
    candidates = set(cells)
    for cell in cells:
        candidates |= neighbors(cell)

    return {
        cell
        for cell in candidates
        if _survives(cell, cells)
    }


def _survives(cell: tuple[int, int], cells: set[tuple[int, int]]) -> bool:
    live_neighbors = sum(1 for n in neighbors(cell) if n in cells)
    if cell in cells:
        return live_neighbors in (2, 3)
    return live_neighbors == 3


# --------------------------------------------------------------------------
# Rendering
# --------------------------------------------------------------------------

def bbox(cells: set[tuple[int, int]]) -> tuple[int, int, int, int] | None:
    """Return (min_x, min_y, max_x, max_y) of the live cells, or None if empty."""
    if not cells:
        return None
    xs = [x for x, _ in cells]
    ys = [y for _, y in cells]
    return min(xs), min(ys), max(xs), max(ys)


def render(cells: set[tuple[int, int]], height: int = 12, width: int = 40,
           origin: tuple[int, int] = (0, 0)) -> str:
    """Render the board to a string, cropping to a viewport.

    ``origin`` is the top-left corner of the viewport in board coordinates.
    """
    ox, oy = origin
    lines = []
    for row in range(oy, oy + height):
        lines.append(
            "".join(
                LIVE if (ox + col, row) in cells else DEAD
                for col in range(width)
            )
        )
    return "\n".join(lines)
