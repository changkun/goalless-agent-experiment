"""
Langton's Ant — multi-ant variant.

Each ant follows two rules:
  On a white cell: turn right, flip the cell, step forward.
  On a black cell: turn left,  flip the cell, step forward.

One ant produces ~10,000 steps of chaos, then spontaneously builds a
diagonal "highway." Multiple ants interact through the shared grid:
each one keeps overwriting the trails the others leave behind, and the
highways either reinforce or annihilate each other depending on phase.
"""

import sys
import time
import shutil

# Direction vectors: 0=N, 1=E, 2=S, 3=W
DX = (0, 1, 0, -1)
DY = (-1, 0, 1, 0)

# ANSI 256-color palette per ant — chosen for high contrast on dark bg.
ANT_COLORS = (196, 46, 51, 226, 201, 208)

CELL_LIVE = "\x1b[48;5;{c}m  \x1b[0m"
CELL_DEAD = "  "
ANT_GLYPH = "\x1b[1;48;5;{c}m\x1b[38;5;15m{a}\x1b[0m"
ARROWS = "^>v<"

CLEAR = "\x1b[H\x1b[2J"
HOME = "\x1b[H"
HIDE_CURSOR = "\x1b[?25l"
SHOW_CURSOR = "\x1b[?25h"


class Ant:
    __slots__ = ("x", "y", "d", "color")

    def __init__(self, x, y, d, color):
        self.x, self.y, self.d, self.color = x, y, d, color


def step(grid, ant, w, h):
    cell = grid[ant.y][ant.x]
    if cell == 0:
        ant.d = (ant.d + 1) % 4  # right
        grid[ant.y][ant.x] = ant.color
    else:
        ant.d = (ant.d - 1) % 4  # left
        grid[ant.y][ant.x] = 0
    ant.x = (ant.x + DX[ant.d]) % w
    ant.y = (ant.y + DY[ant.d]) % h


def render(grid, ants, w, h, generation):
    out = [HOME]
    out.append(f"\x1b[1mgen {generation:>8}\x1b[0m   {len(ants)} ants   "
               f"{w}x{h} torus\n")
    ant_at = {(a.x, a.y): a for a in ants}
    for y in range(h):
        row = []
        for x in range(w):
            a = ant_at.get((x, y))
            if a is not None:
                row.append(ANT_GLYPH.format(c=a.color, a=ARROWS[a.d] + " "))
            else:
                c = grid[y][x]
                row.append(CELL_DEAD if c == 0 else CELL_LIVE.format(c=c))
        out.append("".join(row))
        out.append("\n")
    sys.stdout.write("".join(out))
    sys.stdout.flush()


def main():
    cols, rows = shutil.get_terminal_size((100, 30))
    w = max(20, cols // 2 - 1)
    h = max(15, rows - 3)

    grid = [[0] * w for _ in range(h)]

    # Three ants, scattered, facing different directions — enough interaction
    # without immediately collapsing into a single shared pattern.
    ants = [
        Ant(w // 4,     h // 2, 1, ANT_COLORS[0]),
        Ant(w // 2,     h // 3, 2, ANT_COLORS[1]),
        Ant(3 * w // 4, 2 * h // 3, 0, ANT_COLORS[2]),
    ]

    sys.stdout.write(HIDE_CURSOR + CLEAR)
    try:
        gen = 0
        FRAME_STEPS = 40    # simulation steps per rendered frame
        FRAME_DELAY = 0.03
        while True:
            for _ in range(FRAME_STEPS):
                for a in ants:
                    step(grid, a, w, h)
                gen += 1
            render(grid, ants, w, h, gen)
            time.sleep(FRAME_DELAY)
    except KeyboardInterrupt:
        pass
    finally:
        sys.stdout.write(SHOW_CURSOR + "\n")


if __name__ == "__main__":
    main()
