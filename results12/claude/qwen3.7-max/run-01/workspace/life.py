"""Conway's Game of Life in the terminal.

Rules:
  - A live cell with 2 or 3 neighbors survives.
  - A dead cell with exactly 3 neighbors becomes alive.
  - All other cells die / stay dead.

Controls: Ctrl-C to quit.
"""
import os
import shutil
import sys
import time
from random import random

ALIVE = "##"
DEAD  = "  "


def empty_grid(h: int, w: int) -> list[list[int]]:
    return [[0] * w for _ in range(h)]


def seed(h: int, w: int, density: float = 0.28) -> list[list[int]]:
    return [[1 if random() < density else 0 for _ in range(w)] for _ in range(h)]


def step(g: list[list[int]]) -> list[list[int]]:
    h, w = len(g), len(g[0])
    out = empty_grid(h, w)
    for y in range(h):
        for x in range(w):
            n = 0
            for dy in (-1, 0, 1):
                for dx in (-1, 0, 1):
                    if dy == 0 and dx == 0:
                        continue
                    ny, nx = (y + dy) % h, (x + dx) % w  # toroidal wrap
                    n += g[ny][nx]
            if g[y][x]:
                out[y][x] = 1 if n in (2, 3) else 0
            else:
                out[y][x] = 1 if n == 3 else 0
    return out


def render(g: list[list[int]]) -> str:
    rows = []
    for row in g:
        rows.append("".join(ALIVE if c else DEAD for c in row))
    return "\n".join(rows)


POPULATION = 0
GENERATION = 0


def stats(g: list[list[int]], gen: int) -> str:
    alive = sum(cell for row in g for cell in row)
    return f"  gen {gen:>5}  |  alive {alive:>5}  |  ctrl-c to quit"


def main() -> None:
    global POPULATION, GENERATION
    cols, rows = shutil.get_terminal_size((80, 24))
    # Each cell is 2 chars wide ("##" or "  "); leave 1 row for the status line.
    w = max(20, cols // 2)
    h = max(8, rows - 2)

    g = seed(h, w, density=0.28)
    POPULATION = sum(cell for row in g for cell in row)

    try:
        # Hide the cursor for cleanliness.
        sys.stdout.write("\033[?25l")
        sys.stdout.flush()

        while True:
            sys.stdout.write("\033[H")  # move to home (top-left)
            sys.stdout.write(render(g))
            sys.stdout.write("\n" + stats(g, GENERATION))
            sys.stdout.flush()
            time.sleep(0.08)
            g = step(g)
            GENERATION += 1
    except KeyboardInterrupt:
        pass
    finally:
        sys.stdout.write("\033[?25h")  # restore cursor
        sys.stdout.write("\n")
        sys.stdout.flush()
        print(f"Ended on generation {GENERATION}. Bye!")


if __name__ == "__main__":
    main()
