#!/usr/bin/env python3
"""
Wave Function Collapse — ASCII texture synthesis for the terminal.

Give it a small hand-drawn sample. It learns every NxN patch that appears in
that sample and which patches may sit beside which, then grows a brand new
image that is locally indistinguishable from the original but globally novel.

    ./wfc.py islands -W 60 -H 24
    ./wfc.py --list

Overlapping model, entropy-ordered observation, worklist constraint
propagation over bitmasks, chronological backtracking. No dependencies.
"""

from __future__ import annotations

import argparse
import math
import random
import sys

# Neighbour offsets. compat[d][p] answers "if I am pattern p, which patterns
# may live at my neighbour in direction d?"
DIRS = ((-1, 0), (0, 1), (1, 0), (0, -1))


# --------------------------------------------------------------------------- #
# Samples
# --------------------------------------------------------------------------- #
# symmetry: 1 = as drawn, 2 = mirror horizontally, 4 = rotations, 8 = full
#           dihedral. Only use 4/8 when the glyphs themselves survive rotation
#           ('#' does, '─' very much does not).
# periodic: treat the sample as a torus when harvesting patterns.
# ground:   pin the output's top and bottom rows to patterns that were drawn in
#           the sample's top and bottom rows. Gives a sky and a floor.

SAMPLES = {
    "islands": {
        "blurb": "archipelagos: deep water, beaches, grass, peaks",
        "symmetry": 8,
        "periodic": True,
        "art": """\
~~~~~~~~~~~~~~~~~~~~
~~~~~~~~~~~~~~~~~~~~
~~~~~~,,,,,,~~~~~~~~
~~~~,,......,,~~~~~~
~~~,,...^^^...,~~~~~
~~,,..^^^^^^^..,~~~~
~~,..^^^^^^^^^..,~~~
~~,,..^^^^^^^..,,~~~
~~~,,...^^^...,,~~~~
~~~~,,......,,~~~~~~
~~~~~,,,,,,,,~~~~~~~
~~~~~~~~~~~~~~~~~~~~
~~~~~~~~~~~~~~~~~~~~""",
        "palette": {"~": 25, ",": 179, ".": 71, "^": 250},
    },
    "cave": {
        "blurb": "eroded rock: winding caverns and pillars",
        "symmetry": 8,
        "periodic": True,
        "art": """\
####################
###.....####...#####
##.......##.....####
#....##...#..###..##
#...####..#..####..#
#...####..#...###..#
#....##...##......##
##........#.......##
###......###.....###
####....#####...####
####################""",
        "palette": {"#": 240, ".": 223},
    },
    "circuit": {
        "blurb": "traces, junctions and pads on a board",
        "symmetry": 1,
        "periodic": False,
        "art": """\

  ┌───┐   ┌─────┐
  │   └───┤     │
  │       │  ▚  │
  └──┬────┤     │
     │    └──┬──┘
  ┌──┴──┐    │
  │  ▚  ├────┘
  └─────┘
                    """,
        "palette": {" ": 22, "▚": 226, "─": 84, "│": 84,
                    "┌": 84, "┐": 84, "└": 84, "┘": 84,
                    "┬": 84, "┴": 84, "├": 84, "┤": 84},
    },
    "flowers": {
        "blurb": "a meadow, rooted in soil, growing into sky",
        "symmetry": 2,
        "periodic": False,
        "ground": True,
        "art": """\
..............................
..............................
......o.......................
......|..........o............
.....\\|/.........|............
......|.........\\|/...........
......|..........|.......o....
......|..........|.......|....
##############################
##############################
##############################""",
        "palette": {".": 17, "o": 205, "|": 77, "\\": 77, "/": 77, "#": 94},
    },
    "rooms": {
        "blurb": "a dungeon of chambers and corridors",
        "symmetry": 8,
        "periodic": True,
        "art": """\
###################
#.........#.......#
#.###.###.#.#####.#
#.#.....#...#...#.#
#.#.###.#####.#.#.#
#...#.........#...#
###.#.#########.###
#...#.....#.......#
#.#######.#.#####.#
#.........#.......#
###################""",
        "palette": {"#": 238, ".": 180},
    },
}


# --------------------------------------------------------------------------- #
# Pattern harvesting
# --------------------------------------------------------------------------- #

def _rotate(p, n):
    """Rotate an NxN pattern 90 degrees."""
    return tuple(p[n - 1 - y + x * n] for y in range(n) for x in range(n))


def _reflect(p, n):
    """Mirror an NxN pattern horizontally."""
    return tuple(p[n - 1 - x + y * n] for y in range(n) for x in range(n))


def _variants(p, n, symmetry):
    """The `symmetry` distinct dihedral images of p, in mxgmn's order."""
    out = [p]
    if symmetry >= 2:
        out.append(_reflect(p, n))
    if symmetry >= 4:
        r = _rotate(p, n)
        out += [r, _reflect(r, n)]
    if symmetry >= 8:
        r2 = _rotate(_rotate(p, n), n)
        r3 = _rotate(r2, n)
        out += [r2, _reflect(r2, n), r3, _reflect(r3, n)]
    return out[:symmetry]


def harvest(art, n, symmetry, periodic):
    """Return (patterns, weights, from_top, from_bottom).

    patterns  — list of NxN char tuples, row-major
    weights   — how often each was seen (drives the output's texture)
    from_top / from_bottom — sets of indices seen flush with a sample edge
    """
    rows = art.split("\n")
    width = max(len(r) for r in rows)
    grid = [r.ljust(width) for r in rows]
    height = len(grid)

    ys = range(height) if periodic else range(height - n + 1)
    xs = range(width) if periodic else range(width - n + 1)

    counts, order, from_top, from_bottom = {}, [], set(), set()
    for oy in ys:
        for ox in xs:
            patch = tuple(
                grid[(oy + dy) % height][(ox + dx) % width]
                for dy in range(n)
                for dx in range(n)
            )
            for i, v in enumerate(_variants(patch, n, symmetry)):
                if v not in counts:
                    counts[v] = 0
                    order.append(v)
                counts[v] += 1
                # Edge bookkeeping only makes sense for the undistorted patch.
                if i == 0:
                    if oy == 0:
                        from_top.add(v)
                    if oy == height - n:
                        from_bottom.add(v)

    index = {p: i for i, p in enumerate(order)}
    return (
        order,
        [counts[p] for p in order],
        {index[p] for p in from_top},
        {index[p] for p in from_bottom},
    )


def _agrees(a, b, dx, dy, n):
    """True if pattern b, offset from a by (dx, dy), agrees on the overlap."""
    xlo, xhi = (dx, n) if dx >= 0 else (0, n + dx)
    ylo, yhi = (dy, n) if dy >= 0 else (0, n + dy)
    for y in range(ylo, yhi):
        for x in range(xlo, xhi):
            if a[x + n * y] != b[x - dx + n * (y - dy)]:
                return False
    return True


def compatibility(patterns, n):
    """compat[d][p] = bitmask of patterns allowed at p's neighbour in dir d."""
    table = []
    for dx, dy in DIRS:
        col = []
        for a in patterns:
            mask = 0
            for j, b in enumerate(patterns):
                if _agrees(a, b, dx, dy, n):
                    mask |= 1 << j
            col.append(mask)
        table.append(col)
    return table


# --------------------------------------------------------------------------- #
# Solver
# --------------------------------------------------------------------------- #

class Contradiction(Exception):
    pass


class Wave:
    def __init__(self, weights, compat, w, h, periodic, rng):
        self.weights = weights
        self.compat = compat
        self.w, self.h = w, h
        self.size = w * h
        self.periodic = periodic
        self.rng = rng
        self.full = (1 << len(weights)) - 1
        self.log_w = [wt * math.log(wt) for wt in weights]
        self._union = {}
        self._entropy = {}

    # -- bit helpers -------------------------------------------------------- #

    @staticmethod
    def bits(mask):
        while mask:
            low = mask & -mask
            yield low.bit_length() - 1
            mask ^= low

    def union(self, mask, d):
        """Patterns permitted next to *any* option in mask. Memoised: the same
        masks recur constantly, and this is the propagator's hot loop."""
        key = (mask, d)
        hit = self._union.get(key)
        if hit is None:
            col = self.compat[d]
            hit = 0
            for p in self.bits(mask):
                hit |= col[p]
            self._union[key] = hit
        return hit

    def entropy(self, mask):
        """Shannon entropy of the cell's weighted option distribution."""
        hit = self._entropy.get(mask)
        if hit is None:
            total = sum(self.weights[p] for p in self.bits(mask))
            acc = sum(self.log_w[p] for p in self.bits(mask))
            hit = math.log(total) - acc / total
            self._entropy[mask] = hit
        return hit

    # -- the algorithm ------------------------------------------------------ #

    def observe(self, wave):
        """Least-entropy undecided cell, ties broken by noise. None if done."""
        best, best_cell = math.inf, None
        for i, mask in enumerate(wave):
            if mask & (mask - 1) == 0:  # zero or one bit set: already decided
                continue
            e = self.entropy(mask) + self.rng.random() * 1e-6
            if e < best:
                best, best_cell = e, i
        return best_cell

    def order(self, mask):
        """Options for a cell, weight-shuffled: likely choices tried first."""
        opts = list(self.bits(mask))
        keys = {p: self.rng.random() ** (1.0 / self.weights[p]) for p in opts}
        opts.sort(key=lambda p: -keys[p])
        return opts

    def propagate(self, wave, seed):
        """Shrink neighbours until stable. Raises on an empty cell."""
        work = [seed]
        while work:
            i = work.pop()
            mask = wave[i]
            x, y = i % self.w, i // self.w
            for d, (dx, dy) in enumerate(DIRS):
                nx, ny = x + dx, y + dy
                if self.periodic:
                    nx %= self.w
                    ny %= self.h
                elif not (0 <= nx < self.w and 0 <= ny < self.h):
                    continue
                j = ny * self.w + nx
                before = wave[j]
                after = before & self.union(mask, d)
                if after != before:
                    if after == 0:
                        raise Contradiction
                    wave[j] = after
                    work.append(j)

    def solve(self, seeds=()):
        """Collapse everything. Returns pattern indices per cell, or None."""
        wave = [self.full] * self.size
        for cell, mask in seeds:
            wave[cell] &= mask
            if wave[cell] == 0:
                return None
        try:
            for cell, _ in seeds:
                self.propagate(wave, cell)
        except Contradiction:
            return None

        # Each frame is a decision we can walk back: the wave as it was, the
        # cell we chose, and the options we have not tried yet.
        trail = []
        while True:
            cell = self.observe(wave)
            if cell is None:
                return [m.bit_length() - 1 for m in wave]
            snapshot, options = wave, self.order(wave[cell])
            while True:
                if not options:
                    if not trail:
                        return None  # exhausted: the whole search failed
                    snapshot, cell, options = trail.pop()
                    continue
                trial = list(snapshot)
                trial[cell] = 1 << options.pop(0)
                try:
                    self.propagate(trial, cell)
                except Contradiction:
                    continue  # that guess was wrong; take the next one
                trail.append((snapshot, cell, options))
                wave = trial
                break


# --------------------------------------------------------------------------- #
# Rendering
# --------------------------------------------------------------------------- #

def to_chars(observed, patterns, n, w, h, periodic):
    """Read one glyph out of each cell's chosen pattern.

    Normally that is the pattern's top-left cell. Along a non-wrapping right
    or bottom edge there is no cell beyond, so we walk into the interior of the
    last usable pattern rather than lose the border. Clamping the step keeps
    the source cell on the grid even when w or h is as small as n.
    """
    out = []
    for y in range(h):
        row = []
        for x in range(w):
            if periodic:
                dx = dy = 0
            else:
                dx = min(n - 1, max(0, x - (w - n)))
                dy = min(n - 1, max(0, y - (h - n)))
            p = patterns[observed[(x - dx) + (y - dy) * w]]
            row.append(p[dx + dy * n])
        out.append("".join(row))
    return out


def paint(rows, palette, color):
    if not color:
        return "\n".join(rows)
    out = []
    for row in rows:
        # One escape per run of same-coloured glyphs, not one per glyph.
        buf, last = [], None
        for ch in row:
            c = palette.get(ch)
            if c != last:
                buf.append("\x1b[0m" if c is None else f"\x1b[38;5;{c}m")
                last = c
            buf.append(ch)
        buf.append("\x1b[0m")
        out.append("".join(buf))
    return "\n".join(out)


# --------------------------------------------------------------------------- #
# CLI
# --------------------------------------------------------------------------- #

def main(argv=None):
    ap = argparse.ArgumentParser(
        description="Wave Function Collapse texture synthesis for the terminal.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    ap.add_argument("sample", nargs="?", default="islands",
                    help="which sample to learn from (default: islands)")
    ap.add_argument("-W", "--width", type=int, default=64)
    ap.add_argument("-H", "--height", type=int, default=24)
    ap.add_argument("-n", type=int, default=3, help="patch size (default: 3)")
    ap.add_argument("-s", "--seed", type=int, help="reproduce an exact result")
    ap.add_argument("-t", "--tries", type=int, default=8,
                    help="restarts before giving up (default: 8)")
    ap.add_argument("-p", "--periodic", action="store_true",
                    help="make the output itself tile seamlessly")
    ap.add_argument("--plain", action="store_true", help="disable colour")
    ap.add_argument("--sample-art", action="store_true",
                    help="show the sample instead of generating")
    ap.add_argument("-l", "--list", action="store_true")
    args = ap.parse_args(argv)

    if args.list:
        print("samples:")
        for name, s in SAMPLES.items():
            print(f"  {name:9s} {s['blurb']}")
        return 0

    if args.sample not in SAMPLES:
        print(f"wfc: unknown sample {args.sample!r}; try --list", file=sys.stderr)
        return 2

    spec = SAMPLES[args.sample]
    palette = spec["palette"]
    color = not args.plain and sys.stdout.isatty()

    if args.sample_art:
        print(paint(spec["art"].split("\n"), palette, color))
        return 0

    if args.n < 2:
        print("wfc: -n must be at least 2", file=sys.stderr)
        return 2
    if args.width < args.n or args.height < args.n:
        print(f"wfc: output must be at least {args.n}x{args.n} to fit a patch",
              file=sys.stderr)
        return 2

    patterns, weights, from_top, from_bottom = harvest(
        spec["art"], args.n, spec["symmetry"], spec["periodic"]
    )
    compat = compatibility(patterns, args.n)

    # A ground sample only reads correctly the right way up, so pin the edges.
    # Each cell renders its pattern's top-left glyph, so a patch harvested at
    # the sample's last valid row shows the row n steps above the true floor.
    # Pinning the last n rows is what puts actual soil on screen.
    seeds = []
    if spec.get("ground") and not args.periodic:
        top = sum(1 << p for p in from_top)
        bottom = sum(1 << p for p in from_bottom)
        floor = args.height - args.n
        if top and bottom and floor > args.n:
            full = (1 << len(patterns)) - 1
            for x in range(args.width):
                # Soil below the floor line, and nowhere else: left free, the
                # solid-earth patch is heavy enough to flood the whole frame.
                for y in range(floor, args.height):
                    seeds.append((y * args.width + x, bottom))
                for y in range(1, floor):
                    seeds.append((y * args.width + x, full & ~bottom))
                seeds.append((x, top & ~bottom))

    base = args.seed if args.seed is not None else random.randrange(1 << 30)
    for attempt in range(args.tries):
        seed = base + attempt
        wave = Wave(weights, compat, args.width, args.height,
                    args.periodic, random.Random(seed))
        observed = wave.solve(seeds)
        if observed is not None:
            rows = to_chars(observed, patterns, args.n,
                            args.width, args.height, args.periodic)
            print(paint(rows, palette, color))
            note = (f"{args.sample} · {len(patterns)} patterns · "
                    f"n={args.n} · seed {seed}")
            print(f"\x1b[2m{note}\x1b[0m" if color else f"# {note}",
                  file=sys.stderr)
            return 0

    print(f"wfc: no solution after {args.tries} tries", file=sys.stderr)
    return 1


if __name__ == "__main__":
    sys.exit(main())
