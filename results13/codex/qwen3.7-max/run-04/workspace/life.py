#!/usr/bin/env python3
"""Conway's Game of Life — terminal renderer."""

import random
import sys
import time
from enum import Enum

# ANSI helpers
CLEAR = "\033[2J\033[H"
CELL_ON = "\033[97;10m██"
CELL_OFF = "\033[40m  "
RESET = "\033[0m"


class Pattern(Enum):
    GLIDER = "Glider"
    PULSAR = "Pulsar"
    GOSPER_GLIDER_GUN = "Gosper Glider Gun"
    PENTA_DECATHLON = "Pentadecathlon"
    RANDOM = "Random soup"


# ---- Pattern definitions (relative coords) ----

GLIDER = [(0, 1), (1, 2), (2, 0), (2, 1), (2, 2)]

PULSAR = [
    (0, 2), (0, 3), (0, 4), (0, 8), (0, 9), (0, 10),
    (2, 0), (2, 5), (2, 7), (2, 12),
    (3, 0), (3, 5), (3, 7), (3, 12),
    (4, 0), (4, 5), (4, 7), (4, 12),
    (5, 2), (5, 3), (5, 4), (5, 8), (5, 9), (5, 10),
    (7, 2), (7, 3), (7, 4), (7, 8), (7, 9), (7, 10),
    (8, 0), (8, 5), (8, 7), (8, 12),
    (9, 0), (9, 5), (9, 7), (9, 12),
    (10, 0), (10, 5), (10, 7), (10, 12),
    (12, 2), (12, 3), (12, 4), (12, 8), (12, 9), (12, 10),
]

GOSPER_GLIDER_GUN = [
    (0,24),
    (1,22),(1,24),
    (2,12),(2,13),(2,20),(2,21),(2,34),(2,35),
    (3,11),(3,15),(3,20),(3,21),(3,34),(3,35),
    (4,0),(4,1),(4,10),(4,16),(4,20),(4,21),
    (5,0),(5,1),(5,10),(5,14),(5,16),(5,17),(5,22),(5,24),
    (6,10),(6,16),(6,24),
    (7,11),(7,15),
    (8,12),(8,13),
]

PENTA_DECATHLON = [
    (i, 0) for i in range(10)
]


def place_pattern(grid, pattern, offset_r, offset_c):
    rows, cols = len(grid), len(grid[0])
    for r, c in pattern:
        grid[(r + offset_r) % rows][(c + offset_c) % cols] = True


def step(grid):
    """Compute next generation. Toroidal (wraps around edges)."""
    rows, cols = len(grid), len(grid[0])
    new = [[False] * cols for _ in range(rows)]
    for r in range(rows):
        for c in range(cols):
            n = 0
            for dr in (-1, 0, 1):
                for dc in (-1, 0, 1):
                    if dr == dc == 0:
                        continue
                    if grid[(r + dr) % rows][(c + dc) % cols]:
                        n += 1
            if grid[r][c]:
                new[r][c] = n in (2, 3)
            else:
                new[r][c] = n == 3
    return new


def render(grid, gen, pop):
    rows = len(grid)
    cols = len(grid[0])
    out = [CLEAR]
    out.append(f"\033[1;36mGame of Life\033[0m  \033[33mGen {gen:<6}\033[0m  Pop {pop:<6}")
    out.append("-" * (cols * 2 + 2) + "\n")
    for r in range(rows):
        for c in range(cols):
            out.append(CELL_ON if grid[r][c] else CELL_OFF)
        out.append(RESET + "\n")
    out.append(RESET)
    sys.stdout.write("".join(out))
    sys.stdout.flush()


def pick_scene(cols, rows):
    """Return a populated grid with a nice mix of patterns."""
    grid = [[False] * cols for _ in range(rows)]
    place_pattern(grid, GLIDER, 2, 2)
    place_pattern(grid, PULSAR, rows // 2 - 6, cols // 2 - 6)
    place_pattern(grid, PENTA_DECATHLON, rows // 2, cols // 4)
    place_pattern(grid, GOSPER_GLIDER_GUN, rows // 2 + 4, cols - 36)
    return grid


def main():
    cols = 60
    rows = 24

    # Parse args: optional pattern name
    if "--pattern" in sys.argv:
        idx = sys.argv.index("--pattern")
        name = sys.argv[idx + 1].upper()
        grid = [[False] * cols for _ in range(rows)]
        pats = {
            "GLIDER": (GLIDER, 2, 2),
            "PULSAR": (PULSAR, rows // 2 - 7, cols // 2 - 7),
            "GOSPER": (GOSPER_GLIDER_GUN, rows // 2 - 5, 2),
            "PENTA": (PENTA_DECATHLON, rows // 2, cols // 2 - 1),
        }
        if name in pats:
            pat, ofr, ofc = pats[name]
            place_pattern(grid, pat, ofr, ofc)
        else:
            print(f"Unknown pattern: {name}. Choices: {list(pats.keys())}")
            sys.exit(1)
    else:
        grid = pick_scene(cols, rows)

    gen = 0
    try:
        while True:
            pop = sum(cell for row in grid for cell in row)
            render(grid, gen, pop)
            grid = step(grid)
            gen += 1
            time.sleep(0.08)
    except KeyboardInterrupt:
        print(f"\n\033[0mStopped at generation {gen}. Goodbye!")


if __name__ == "__main__":
    main()
