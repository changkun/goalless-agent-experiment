"""Classic Life patterns as coordinate sets.

Each pattern's bounding box is roughly centered on the origin so patterns
composed together (e.g. via ``patterns_at``) line up naturally.
"""

from __future__ import annotations


def _coords(spec: list[str]) -> set[tuple[int, int]]:
    """Turn ASCII art into cell coordinates, centered on the origin."""
    height = len(spec)
    width = max(len(row) for row in spec)
    cells: set[tuple[int, int]] = set()
    for y, row in enumerate(spec):
        for x, ch in enumerate(row):
            if ch == "O":
                # Center: subtract half the bounding box, rounded down.
                cells.add((x - width // 2, y - height // 2))
    return cells


# Still lifes: do not change between generations.
BLOCK = _coords(["OO", "OO"])
BEEHIVE = _coords([
    ".OO.",
    "O..O",
    ".OO.",
])

# Oscillators: return to their original shape after a period.
BLINKER = _coords(["OOO"])
TOAD = _coords([
    ".OOO",
    "OOO.",
])
PULSAR = _coords([
    "..OOO...OOO..",
    ".............",
    "O....O.O....O",
    "O....O.O....O",
    "O....O.O....O",
    "..OOO...OOO..",
    ".............",
    "..OOO...OOO..",
    "O....O.O....O",
    "O....O.O....O",
    "O....O.O....O",
    ".............",
    "..OOO...OOO..",
])

# Spaceships: translate themselves across the board over time.
GLIDER = _coords([
    ".O.",
    "..O",
    "OOO",
])

ALL_PATTERNS: dict[str, set[tuple[int, int]]] = {
    "block": BLOCK,
    "beehive": BEEHIVE,
    "blinker": BLINKER,
    "toad": TOAD,
    "pulsar": PULSAR,
    "glider": GLIDER,
}


def patterns_at(cells_by_name: dict[str, set[tuple[int, int]]],
                offset: tuple[int, int] = (0, 0)) -> set[tuple[int, int]]:
    """Compose several named patterns into one board, offset by ``offset``."""
    dx, dy = offset
    merged: set[tuple[int, int]] = set()
    for name, pattern in cells_by_name.items():
        try:
            coords = ALL_PATTERNS[name]
        except KeyError:
            raise ValueError(f"unknown pattern: {name!r}") from None
        merged |= {(x + dx, y + dy) for x, y in coords}
    return merged
