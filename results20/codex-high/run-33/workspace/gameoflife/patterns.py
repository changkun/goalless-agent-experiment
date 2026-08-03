"""Classic Game of Life patterns, defined as multiline ASCII art.

Each pattern is a list of strings where each character is either 'O' (live)
or anything else (dead).  The top-left corner of the art maps to the origin
of the coordinate system (0, 0) with y growing downward.
"""

from __future__ import annotations

from typing import List, Sequence, Tuple

from .engine import Cell

Pattern = Sequence[str]

_PATTERNS: dict[str, Pattern] = {
    "Glider": [
        ".O.",
        "..O",
        "OOO",
    ],
    "Gosper Glider Gun": [
        "........................O...........",
        "......................O.O...........",
        "............OO......OO............OO",
        "...........O...O....OO............OO",
        "OO........O.....O...OO..............",
        "OO........O...O.OO....O.O...........",
        "..........O.....O.......O...........",
        "...........O...O....................",
        "............OO......................",
    ],
    "Pulsar": [
        "..OOO...OOO..",
        "...........",
        "O....O.O....O",
        "O....O.O....O",
        "O....O.O....O",
        "..OOO...OOO..",
        "...........",
        "O....O.O....O",
        "O....O.O....O",
        "O....O.O....O",
        "...........",
        "..OOO...OOO..",
    ],
    "R-pentomino": [
        ".OO",
        "OO.",
        ".O.",
    ],
    "Acorn": [
        ".O.....",
        "...O...",
        "OO..OOO",
    ],
    "Diehard": [
        "......O.",
        "OO......",
        ".O...OOO",
    ],
    "Blinker": [
        "OOO",
    ],
    "Beacon": [
        "OO..",
        "O...",
        "...O",
        "..OO",
    ],
    "Toad": [
        ".OOO",
        "OOO.",
    ],
    "Block": [
        "OO",
        "OO",
    ],
    "Pi-heptomino": [
        "OOO",
        "O.O",
        "O.O",
    ],
    "LWSS": [
        ".O..O",
        "O....",
        "O...O",
        "OOOO.",
    ],
    "MWSS": [
        ".OO.O",
        "O....",
        "O...O",
        "OOOO.",
    ],
    "HWSS": [
        ".OO..O",
        "O.....",
        "O....O",
        "OOOOO.",
    ],
}

# Drop any accidental empty rows so cell coordinates stay predictable.
_PATTERNS = {
    name: [row for row in rows if row]
    for name, rows in _PATTERNS.items()
}


def names() -> List[str]:
    """Return the available pattern names in a stable order."""
    return list(_PATTERNS.keys())


def load(name: str) -> List[Cell]:
    """Return the live cells for a named pattern relative to the origin."""
    rows = _PATTERNS[name]
    cells: List[Cell] = []
    for y, row in enumerate(rows):
        for x, ch in enumerate(row):
            if ch == "O":
                cells.append((x, y))
    return cells


def center(pattern: Pattern) -> Tuple[int, int]:
    """Return (width, height) used to center a pattern on the grid."""
    width = max(len(row) for row in pattern) if pattern else 0
    return (width, len(pattern))
