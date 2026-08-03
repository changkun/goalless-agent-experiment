"""Core Game of Life logic — a dependency-free, grid-based implementation.

Cells live on an infinite grid represented as a set of (row, col) pairs, so
patterns may drift off the initial bounding box (gliders) without clipping.
"""
from __future__ import annotations

from collections.abc import Iterable, Iterator

# A live cell is represented by its (row, col) coordinate.
Grid = set[tuple[int, int]]


def neighbors(cell: tuple[int, int]) -> Iterator[tuple[int, int]]:
    """Yield the eight cells surrounding *cell* (Moore neighborhood)."""
    r, c = cell
    for dr in (-1, 0, 1):
        for dc in (-1, 0, 1):
            if dr or dc:
                yield (r + dr, c + dc)


def next_generation(grid: Grid) -> Grid:
    """Return the next generation of *grid* per Conway's rules."""
    live = set(grid)
    # Only cells adjacent to (or on) a live cell can change.
    candidates: set[tuple[int, int]] = set(live)
    for cell in live:
        candidates.update(neighbors(cell))

    next_gen: Grid = set()
    for cell in candidates:
        n = sum(1 for nb in neighbors(cell) if nb in live)
        if cell in live:
            if n in (2, 3):  # survival
                next_gen.add(cell)
        elif n == 3:  # birth
            next_gen.add(cell)
    return next_gen


def parse(text: str, alive: str = "#") -> Grid:
    """Parse an ASCII pattern where *alive* marks live cells."""
    grid: Grid = set()
    for row, line in enumerate(text.splitlines()):
        for col, ch in enumerate(line):
            if ch == alive:
                grid.add((row, col))
    return grid


def render(grid: Grid, dead: str = ".", alive: str = "#") -> str:
    """Render *grid* as a newline-terminated ASCII picture."""
    if not grid:
        return ""
    rows = [r for r, _ in grid]
    cols = [c for _, c in grid]
    min_r, max_r = min(rows), max(rows)
    min_c, max_c = min(cols), max(cols)

    lines = [
        "".join(alive if (r, c) in grid else dead for c in range(min_c, max_c + 1))
        for r in range(min_r, max_r + 1)
    ]
    return "\n".join(lines) + "\n"


def blinker() -> Grid:
    """A period-2 oscillator: a horizontal line of three cells."""
    return parse("###")


def glider() -> Grid:
    """A seed that translates diagonally across the grid."""
    return parse(
        """
        .#.
        ..#
        ###
        """
    )


# Convenience: accept an iterable of cells or a Grid-style set interchangeably.
def _coerce(pattern: Iterable[tuple[int, int]] | str) -> Grid:
    if isinstance(pattern, str):
        return parse(pattern)
    return set(pattern)
