"""Conway's Game of Life: the simulation engine.

The engine is deliberately pure and side-effect free so it can be tested
in isolation and reused by any frontend (terminal, web, PNG, ...).

A universe is represented as a set of (x, y) integer coordinates that are
currently alive. Storing only live cells keeps memory proportional to the
population rather than the bounding box, and makes the boundary conditions
explicit: the universe is unbounded (cells can drift off in any direction).
"""

from collections import Counter

#: The 8 neighbour offsets for a cell.
_NEIGHBOURS = [
    (-1, -1), (0, -1), (1, -1),
    (-1,  0),          (1,  0),
    (-1,  1), (0,  1), (1,  1),
]


def step(live):  # live: set[tuple[int, int]] -> set[tuple[int, int]]
    """Advance the universe by one generation.

    Rules (applied simultaneously to every cell):
      1. A live cell with 2 or 3 live neighbours survives.
      2. Otherwise it dies (loneliness or overcrowding).
      3. A dead cell with exactly 3 live neighbours is born.
    """
    # Count how many live neighbours every cell-of-interest has. A cell only
    # needs to be *considered* if it is live, or it neighbours a live cell —
    # anything else has zero live neighbours and stays dead.
    neighbour_count = Counter()
    for x, y in live:
        for dx, dy in _NEIGHBOURS:
            neighbour_count[(x + dx, y + dy)] += 1

    # Born: dead cells (not currently live) with exactly 3 neighbours.
    newborn = {
        coords for coords, n in neighbour_count.items()
        if coords not in live and n == 3
    }
    # Survive: live cells with 2 or 3 neighbours.
    survivors = {
        coords for coords, n in neighbour_count.items()
        if coords in live and n in (2, 3)
    }
    return survivors | newborn


def step_n(initial, generations):
    """Run ``generations`` steps, returning the universe at each step.

    Yields the initial state first, then one set per generation, so callers
    can stream a full animation.
    """
    universe = initial
    yield universe
    for _ in range(generations):
        universe = step(universe)
        yield universe
