"""A library of classic Game of Life patterns.

Coordinates are (x, y) offsets relative to the pattern's top-left.
"""

PATTERNS = {
    "glider": [(1, 0), (2, 1), (0, 2), (1, 2), (2, 2)],
    "lwss": [
        (1, 0), (4, 0),
        (0, 1),
        (0, 2), (4, 2),
        (0, 3), (1, 3), (2, 3), (3, 3),
    ],
    "blinker": [(0, 0), (1, 0), (2, 0)],
    "toad": [(1, 0), (2, 0), (3, 0), (0, 1), (1, 1), (2, 1)],
    "beacon": [(0, 0), (1, 0), (0, 1), (1, 1), (2, 2), (3, 2), (2, 3), (3, 3)],
    "pulsar": [
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
    ],
    "block": [(0, 0), (1, 0), (0, 1), (1, 1)],
    "beehive": [(1, 0), (2, 0), (0, 1), (3, 1), (1, 2), (2, 2)],
    "loaf": [(1, 0), (2, 0), (0, 1), (3, 1), (1, 2), (3, 2), (2, 3)],
    "boat": [(0, 0), (1, 0), (0, 1), (2, 1), (1, 2)],
    "tub": [(1, 0), (0, 1), (2, 1), (1, 2)],
    "rpentomino": [(1, 0), (2, 0), (0, 1), (1, 1), (1, 2)],
    "acorn": [(1, 0), (3, 1), (0, 2), (1, 2), (4, 2), (5, 2), (6, 2)],
    "diehard": [(6, 0), (0, 1), (1, 1), (1, 2), (5, 2), (6, 2), (7, 2)],
    "gosper_gun": [
        (24, 0),
        (22, 1), (24, 1),
        (12, 2), (13, 2), (20, 2), (21, 2), (34, 2), (35, 2),
        (11, 3), (15, 3), (20, 3), (21, 3), (34, 3), (35, 3),
        (0, 4), (1, 4), (10, 4), (16, 4), (20, 4), (21, 4),
        (0, 5), (1, 5), (10, 5), (14, 5), (16, 5), (17, 5), (22, 5), (24, 5),
        (10, 6), (16, 6), (24, 6),
        (11, 7), (15, 7),
        (12, 8), (13, 8),
    ],
}


def get(name):
    """Return a fresh copy of a pattern's cell list, or raise KeyError."""
    if name not in PATTERNS:
        raise KeyError(
            f"unknown pattern {name!r}; choices: {', '.join(sorted(PATTERNS))}"
        )
    return list(PATTERNS[name])


def stamp(grid, name, x=0, y=0):
    """Place a pattern onto a grid with wrap-around."""
    for dx, dy in get(name):
        grid.set(x + dx, y + dy, 1)


def bounds(cells):
    """(width, height) of the bounding box of a cell list."""
    xs = [c[0] for c in cells]
    ys = [c[1] for c in cells]
    return max(xs) - min(xs) + 1, max(ys) - min(ys) + 1
