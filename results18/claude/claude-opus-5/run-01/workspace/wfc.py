#!/usr/bin/env python3
"""Wave Function Collapse over a socket-matched tileset of box-drawing pipes.

The algorithm is the classic three-step loop:

  observe    pick the undecided cell with the lowest Shannon entropy and
             collapse it to a single tile (weighted random choice)
  propagate  push the consequences of that choice outward until every cell's
             domain is arc-consistent with its four neighbours
  repeat     until every cell is decided, backtracking whenever propagation
             empties some cell's domain

Compatibility is never written out by hand. Each tile declares a socket on
each of its four edges, and two tiles may sit side by side iff their facing
sockets are equal. Socket 0 is "no pipe", 1 is a thin line, 2 is a thick one,
so thin and thick pipes form two networks that can never splice into each
other -- a property that falls out of the socket equality rule for free.

Domains are integer bitmasks: bit i set means "tile i is still possible here".

    python3 wfc.py --width 60 --height 20 --seed 7 --color
"""

from __future__ import annotations

import argparse
import math
import random
import sys
from dataclasses import dataclass

# Edge order used everywhere: N, E, S, W.
N, E, S, W = 0, 1, 2, 3
OPPOSITE = (S, W, N, E)
DELTA = ((0, -1), (1, 0), (0, 1), (-1, 0))  # (dx, dy) per direction

NONE, THIN, THICK = 0, 1, 2


@dataclass(frozen=True)
class Tile:
    glyph: str
    sockets: tuple[int, int, int, int]  # N, E, S, W
    weight: float


# Blank is heavily weighted so the pipes get room to breathe; crossings are
# rare so the output reads as routed lines rather than as noise.
TILES: tuple[Tile, ...] = (
    Tile(" ", (NONE, NONE, NONE, NONE), 12.0),
    # thin
    Tile("│", (THIN, NONE, THIN, NONE), 5.0),
    Tile("─", (NONE, THIN, NONE, THIN), 5.0),
    Tile("└", (THIN, THIN, NONE, NONE), 3.0),
    Tile("┘", (THIN, NONE, NONE, THIN), 3.0),
    Tile("┐", (NONE, NONE, THIN, THIN), 3.0),
    Tile("┌", (NONE, THIN, THIN, NONE), 3.0),
    Tile("├", (THIN, THIN, THIN, NONE), 1.0),
    Tile("┤", (THIN, NONE, THIN, THIN), 1.0),
    Tile("┬", (NONE, THIN, THIN, THIN), 1.0),
    Tile("┴", (THIN, THIN, NONE, THIN), 1.0),
    Tile("┼", (THIN, THIN, THIN, THIN), 0.4),
    # thick
    Tile("┃", (THICK, NONE, THICK, NONE), 3.0),
    Tile("━", (NONE, THICK, NONE, THICK), 3.0),
    Tile("┗", (THICK, THICK, NONE, NONE), 2.0),
    Tile("┛", (THICK, NONE, NONE, THICK), 2.0),
    Tile("┓", (NONE, NONE, THICK, THICK), 2.0),
    Tile("┏", (NONE, THICK, THICK, NONE), 2.0),
    Tile("┣", (THICK, THICK, THICK, NONE), 0.6),
    Tile("┫", (THICK, NONE, THICK, THICK), 0.6),
    Tile("┳", (NONE, THICK, THICK, THICK), 0.6),
    Tile("┻", (THICK, THICK, NONE, THICK), 0.6),
    Tile("╋", (THICK, THICK, THICK, THICK), 0.25),
)

NT = len(TILES)
FULL = (1 << NT) - 1
WEIGHTS = [t.weight for t in TILES]
# Precomputed terms of the Shannon entropy of the (unnormalised) weights.
WLOG = [w * math.log(w) for w in WEIGHTS]

# COMPAT[d][i] = bitmask of tiles that may occupy the neighbour of a cell in
# direction d, given that cell holds tile i.
COMPAT: list[list[int]] = [[0] * NT for _ in range(4)]
for d in range(4):
    for i, a in enumerate(TILES):
        mask = 0
        for j, b in enumerate(TILES):
            if a.sockets[d] == b.sockets[OPPOSITE[d]]:
                mask |= 1 << j
        COMPAT[d][i] = mask

# Tiles with no pipe leaving a given edge -- used to seal the grid border so
# nothing dangles off the canvas.
CLOSED_ON: list[int] = [
    sum(1 << i for i, t in enumerate(TILES) if t.sockets[d] == NONE) for d in range(4)
]


def popcount(x: int) -> int:
    return x.bit_count()


class Contradiction(Exception):
    """Propagation emptied a cell's domain."""


class Wave:
    def __init__(self, width: int, height: int, rng: random.Random) -> None:
        self.w, self.h = width, height
        self.rng = rng
        self.cells = [FULL] * (width * height)
        # Seal the border: cells on an edge may only hold tiles closed on that
        # side. Done before any observation so the constraint is global.
        for y in range(height):
            for x in range(width):
                m = FULL
                if y == 0:
                    m &= CLOSED_ON[N]
                if x == width - 1:
                    m &= CLOSED_ON[E]
                if y == height - 1:
                    m &= CLOSED_ON[S]
                if x == 0:
                    m &= CLOSED_ON[W]
                self.cells[y * width + x] = m
        self.propagate(list(range(len(self.cells))))

    # -- entropy ---------------------------------------------------------
    def entropy(self, mask: int) -> float:
        total = 0.0
        acc = 0.0
        m = mask
        while m:
            b = m & -m
            i = b.bit_length() - 1
            total += WEIGHTS[i]
            acc += WLOG[i]
            m ^= b
        return math.log(total) - acc / total

    def lowest_entropy_cell(self) -> int | None:
        """Index of the most-constrained undecided cell, or None if done."""
        best, best_key = None, math.inf
        for idx, mask in enumerate(self.cells):
            if popcount(mask) <= 1:
                continue
            # A pinch of noise breaks ties, which is what keeps successive
            # runs with different seeds from sharing a skeleton.
            key = self.entropy(mask) + self.rng.random() * 1e-6
            if key < best_key:
                best, best_key = idx, key
        return best

    # -- the loop --------------------------------------------------------
    def propagate(self, stack: list[int]) -> None:
        w, h, cells = self.w, self.h, self.cells
        while stack:
            idx = stack.pop()
            mask = cells[idx]
            if mask == 0:
                raise Contradiction
            x, y = idx % w, idx // w
            for d in range(4):
                dx, dy = DELTA[d]
                nx, ny = x + dx, y + dy
                if not (0 <= nx < w and 0 <= ny < h):
                    continue
                # Everything the neighbour is still allowed to be, given every
                # tile this cell could still be.
                allowed = 0
                m = mask
                cd = COMPAT[d]
                while m:
                    b = m & -m
                    allowed |= cd[b.bit_length() - 1]
                    m ^= b
                nidx = ny * w + nx
                before = cells[nidx]
                after = before & allowed
                if after != before:
                    if after == 0:
                        raise Contradiction
                    cells[nidx] = after
                    stack.append(nidx)

    def pick(self, mask: int) -> list[int]:
        """Tile indices in mask, shuffled in weighted-random order."""
        options = []
        m = mask
        while m:
            b = m & -m
            options.append(b.bit_length() - 1)
            m ^= b
        order = []
        pool = options[:]
        while pool:
            total = sum(WEIGHTS[i] for i in pool)
            r = self.rng.random() * total
            for i in pool:
                r -= WEIGHTS[i]
                if r <= 0:
                    break
            order.append(i)
            pool.remove(i)
        return order

    def solve(self) -> int:
        """Collapse the whole grid. Returns the number of backtracks taken."""
        backtracks = 0
        # Explicit stack of decision points, so a contradiction rewinds to the
        # last choice with untried options instead of restarting from scratch.
        trail: list[tuple[list[int], int, list[int]]] = []
        while True:
            idx = self.lowest_entropy_cell()
            if idx is None:
                return backtracks
            snapshot = self.cells[:]
            options = self.pick(self.cells[idx])
            trail.append((snapshot, idx, options))

            while trail:
                snapshot, idx, options = trail[-1]
                if not options:
                    trail.pop()
                    backtracks += 1
                    continue
                tile = options.pop(0)
                self.cells = snapshot[:]
                self.cells[idx] = 1 << tile
                try:
                    self.propagate([idx])
                except Contradiction:
                    backtracks += 1
                    continue
                break
            else:
                raise RuntimeError("tileset admits no solution for this grid")

    # -- output ----------------------------------------------------------
    def rows(self) -> list[str]:
        out = []
        for y in range(self.h):
            row = []
            for x in range(self.w):
                mask = self.cells[y * self.w + x]
                row.append(TILES[mask.bit_length() - 1].glyph if mask else "?")
            out.append("".join(row))
        return out


THIN_GLYPHS = frozenset("│─└┘┐┌├┤┬┴┼")


def colorize(rows: list[str]) -> list[str]:
    dim, bright, reset = "\x1b[38;5;66m", "\x1b[38;5;180m", "\x1b[0m"
    painted = []
    for row in rows:
        buf, mode = [], None
        for ch in row:
            want = dim if ch in THIN_GLYPHS else (bright if ch != " " else None)
            if want != mode:
                buf.append(reset if want is None else want)
                mode = want
            buf.append(ch)
        buf.append(reset)
        painted.append("".join(buf))
    return painted


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument("--width", type=int, default=64)
    p.add_argument("--height", type=int, default=18)
    p.add_argument("--seed", type=int, default=None)
    p.add_argument("--color", action="store_true", help="ANSI-colour the output")
    p.add_argument("--stats", action="store_true", help="report solver work")
    a = p.parse_args(argv)

    seed = a.seed if a.seed is not None else random.randrange(1 << 30)
    wave = Wave(a.width, a.height, random.Random(seed))
    backtracks = wave.solve()

    rows = wave.rows()
    print("\n".join(colorize(rows) if a.color else rows))
    if a.stats:
        filled = sum(ch != " " for row in rows for ch in row)
        print(
            f"\nseed {seed}  {a.width}x{a.height}  "
            f"{backtracks} backtrack(s)  {filled} pipe cells",
            file=sys.stderr,
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
