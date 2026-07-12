"""A handful of classic Game of Life starting patterns.

Each pattern is a set of (x, y) coordinates relative to an arbitrary
origin, ready to be passed into ``Board.from_coordinates`` or offset
with ``Board.translated``.
"""

from __future__ import annotations

PATTERNS: dict[str, set[tuple[int, int]]] = {
    "glider": {(1, 0), (2, 1), (0, 2), (1, 2), (2, 2)},
    "blinker": {(0, 1), (1, 1), (2, 1)},
    "toad": {(1, 0), (2, 0), (3, 0), (0, 1), (1, 1), (2, 1)},
    "beacon": {
        (0, 0), (1, 0), (0, 1),
        (3, 2), (2, 3), (3, 3),
    },
    "lightweight_spaceship": {
        (1, 0), (4, 0),
        (0, 1),
        (0, 2), (4, 2),
        (0, 3), (1, 3), (2, 3), (3, 3),
    },
    "pulsar": {
        (2, 0), (3, 0), (4, 0), (8, 0), (9, 0), (10, 0),
        (0, 2), (5, 2), (7, 2), (12, 2),
        (0, 3), (5, 3), (7, 3), (12, 3),
        (0, 4), (5, 4), (7, 4), (12, 4),
        (2, 5), (3, 5), (4, 5), (8, 5), (9, 5), (10, 5),
        (2, 7), (3, 7), (4, 7), (8, 7), (9, 7), (10, 7),
        (0, 8), (5, 8), (7, 8), (12, 8),
        (0, 9), (5, 9), (7, 9), (12, 9),
        (0, 10), (5, 10), (7, 10), (12, 10),
        (2, 12), (3, 12), (4, 12), (8, 12), (9, 12), (10, 12),
    },
}
