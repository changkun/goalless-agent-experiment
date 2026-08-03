#!/usr/bin/env python3
"""Terminal Game of Life.

A dependency-free, animated take on Conway's Game of Life rendered with
half-block characters for a crisper look. Pick a preset or provide a
custom RLE-encoded pattern on the command line.
"""

import os
import sys
import time
import argparse
from collections import deque
from itertools import product

# ── Rendering ────────────────────────────────────────────────────────────────
# Upper/lower half-block cells give 2:1 vertical resolution per character.
# We track a grid of booleans and map 2 rows of cells into one text row.
ALIVE = "█"
DEAD = " "

class Life:
    def __init__(self, w, h, cells):
        """cells: set of (x, y) alive coordinates, x in [0,w), y in [0,h)."""
        self.w, self.h = w, h
        self.cells = set(cells)
        self.generation = 0

    def step(self):
        """Advance one generation, returning the number of cells born/died."""
        neighbors = {}
        for x, y in self.cells:
            for dx in (-1, 0, 1):
                for dy in (-1, 0, 1):
                    if dx == 0 and dy == 0:
                        continue
                    n = ((x + dx) % self.w, (y + dy) % self.h)  # wrap edges
                    neighbors[n] = neighbors.get(n, 0) + 1

        born = died = 0
        new_cells = set()
        for (x, y), count in neighbors.items():
            if count == 3 or (count == 2 and (x, y) in self.cells):
                new_cells.add((x, y))
            elif (x, y) in self.cells:
                died += 1
        born = len(new_cells) - len(self.cells & new_cells)
        self.cells = new_cells
        self.generation += 1
        return born, died

    def render(self):
        """Two terminal rows of cells per block row (upper/lower half)."""
        rows = []
        for by in range(self.h // 2):
            row = []
            for x in range(self.w):
                top = (x, by * 2) in self.cells      # upper half-block
                bot = (x, by * 2 + 1) in self.cells  # lower half-block
                row.append("█" if top and bot else
                           "▀" if top else
                           "▄" if bot else " ")
            rows.append("".join(row))
        return "\n".join(rows)

# ── Patterns ─────────────────────────────────────────────────────────────────
def glider_gun(w, h, x0=2, y0=4):
    src = """24bo$$22bobo$$12b2o6b2o12b2o$$11bo3bo4b2o12b2o$$2o8bo5bo3b2o14bobo$$
2o8bo3bob2o4bobo12b2o$$10bo5bo7bo$$11bo5bo6bobo$$12b5o7b2o$$14bo"""
    return rle_to_cells(src, w, h, x0, y0)

def pulsar(w, h, x0=0, y0=0):
    src = """2b3o2b3o2$o4bobobobo4bo$o4bobobobo4bo$o4bobobobo4bo$2b3o2b3o2$2b3o2b3o2$
o4bobobobo4bo$o4bobobobo4bo$o4bobobobo4bo$2b3o2b3o"""
    return rle_to_cells(src, w, h, x0, y0)

def rle_to_cells(rle, w, h, x0=0, y0=0):
    """Parse a minimal run-length-encoded block ($ newline, b dead, o alive)."""
    cells, x, y = set(), 0, 0
    count = ""
    for ch in rle:
        if ch.isdigit():
            count += ch
            continue
        n = int(count) if count else 1
        if ch == "b":
            x += n
        elif ch == "o":
            for _ in range(n):
                cells.add(((x0 + x) % w, (y0 + y) % h))
                x += 1
        elif ch == "$":
            x = 0
            y += n
        count = ""
    return cells

PATTERNS = {
    "gun":   glider_gun,   # infinite stream of gliders
    "pulsar": pulsar,      # symmetric period-3 oscillator
    "random": lambda w, h: {(x, y)
                            for y in range(h) for x in range(w)
                            if (x * 31 + y * 17) % 5 == 0},
}

def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("pattern", nargs="?", default="gun",
                    choices=sorted(PATTERNS), help="starting pattern preset")
    ap.add_argument("--w", type=int, default=100, metavar="N", help="grid width")
    ap.add_argument("--h", type=int, default=50, metavar="N", help="grid height")
    ap.add_argument("--fps", type=float, default=30, help="frames per second")
    ap.add_argument("--gens", type=int, default=0,
                    help="stop after N generations (0 = run forever)")
    args = ap.parse_args()

    if args.h % 2:
        args.h += 1  # keep block-to-row mapping exact

    cells = PATTERNS[args.pattern](args.w, args.h)
    life = Life(args.w, args.h, cells)
    frame = 1.0 / args.fps
    try:
        while True:
            os.system("clear")  # or "cls" on Windows
            print("\033[?25l", end="")  # hide cursor
            print(f"  {args.pattern}  •  gen {life.generation}"
                  f"  •  population {len(life.cells)}".ljust(args.w))
            print(life.render())
            sys.stdout.flush()
            time.sleep(frame)
            if args.gens and life.generation >= args.gens:
                break
            life.step()
    except KeyboardInterrupt:
        pass
    finally:
        print("\033[?25h", end="")  # restore cursor
        print("\nbye! ✨")

if __name__ == "__main__":
    main()
