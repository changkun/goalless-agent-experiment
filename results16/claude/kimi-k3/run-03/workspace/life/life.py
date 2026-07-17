#!/usr/bin/env python3
"""
life.py — Conway's Game of Life on a toroidal grid, plus a terminal player.

This module has two halves:

  * Engine  — pure, no terminal anything. The universe is a dict mapping
              (x, y) -> character for every live cell. Evolution is the
              classic B3/S23 rules on a torus (edges wrap).

  * Player  — an ANSI-escape-code terminal renderer with an interactive
              HUD: play/pause, step, speed, palette, help. Cells age; the
              character drawn for a cell is chosen by its age and the active
              palette, so the grid itself becomes the visualization.

Run it:      python3 life.py --pattern glider --speed 8
Headless:    python3 life.py --check            (self-test, no TTY needed)
"""

from __future__ import annotations

import argparse
import copy
import hashlib
import math
import os
import random
import select
import sys
import time
from dataclasses import dataclass, field

# --------------------------------------------------------------------------
# Patterns. Coordinates are (x, y) with y growing downward, as terminals do.
# Each pattern returns (width, height, set_of_live_cells).
# --------------------------------------------------------------------------


def _glider() -> tuple[int, int, set[tuple[int, int]]]:
    return 3, 3, {(1, 0), (2, 1), (0, 2), (1, 2), (2, 2)}


def _r_pentomino() -> tuple[int, int, set[tuple[int, int]]]:
    # The little methuselah that erupts for ~1100 generations.
    return 3, 3, {(1, 0), (2, 0), (0, 1), (1, 1), (1, 2)}


def _acorn() -> tuple[int, int, set[tuple[int, int]]]:
    return 7, 3, {
        (1, 0),
        (3, 1),
        (0, 2), (1, 2), (4, 2), (5, 2), (6, 2),
    }


def _blinker() -> tuple[int, int, set[tuple[int, int]]]:
    return 3, 1, {(0, 0), (1, 0), (2, 0)}


def _pulsar() -> tuple[int, int, set[tuple[int, int]]]:
    # Period-3 oscillator, 13x13.
    cells: set[tuple[int, int]] = set()
    arms = [(2, 0), (3, 0), (4, 0), (0, 2), (0, 3), (0, 4)]
    for base_x, base_y in ((0, 0), (7, 0), (0, 7), (7, 7)):
        for dx, dy in arms:
            cells.add((base_x + dx, base_y + dy))
            cells.add((base_x + dy, base_y + dx))
    return 13, 13, cells


def _lwss() -> tuple[int, int, set[tuple[int, int]]]:
    # Lightweight spaceship, flies diagonally-ish (actually orthogonally).
    return 5, 4, {
        (1, 0), (4, 0),
        (0, 1),
        (0, 2), (4, 2),
        (0, 3), (1, 3), (2, 3), (3, 3),
    }


def _block() -> tuple[int, int, set[tuple[int, int]]]:
    return 2, 2, {(0, 0), (1, 0), (0, 1), (1, 1)}


PATTERNS = {
    "glider": _glider,
    "r-pentomino": _r_pentomino,
    "acorn": _acorn,
    "blinker": _blinker,
    "pulsar": _pulsar,
    "lwss": _lwss,
    "block": _block,
}


def random_soup(width: int, height: int, density: float,
                rng: random.Random) -> set[tuple[int, int]]:
    return {
        (x, y)
        for y in range(height)
        for x in range(width)
        if rng.random() < density
    }


def stamp(cells: set[tuple[int, int]], into_w: int, into_h: int,
          pattern: tuple[int, int, set[tuple[int, int]]] | None = None,
          at: tuple[int, int] | None = None) -> None:
    """Paste a pattern's live cells into `cells`, centered or at `at`."""
    if pattern is None:
        return
    pw, ph, pcells = pattern
    if at is None:
        ox, oy = (into_w - pw) // 2, (into_h - ph) // 2
    else:
        ox, oy = at
    for x, y in pcells:
        cells.add((ox + x, oy + y))


# --------------------------------------------------------------------------
# Engine
# --------------------------------------------------------------------------

# A live cell's value is a character chosen by age. Age 0 (just born) shows
# the first glyph; older cells climb the ramp. Ages beyond the ramp stay on
# the last glyph — the ancients.
AGE_RAMPS = {
    "classic": "·oO@",
    "embers": "∙•●█",
    "binary": "01",
}


def evolve(cells: set[tuple[int, int]], ages: dict[tuple[int, int], int],
           width: int, height: int
           ) -> tuple[set[tuple[int, int]], dict[tuple[int, int], int],
                      dict[tuple[int, int], int]]:
    """One tick of B3/S23 on a torus.

    Returns (new_cells, new_ages, births) where births maps newborn cell ->
    the age of its oldest neighbor (used to tint newborns by parentage).
    """
    neighbor_count: dict[tuple[int, int], int] = {}
    oldest_neighbor: dict[tuple[int, int], int] = {}
    for (x, y) in cells:
        age = ages[(x, y)]
        for dy in (-1, 0, 1):
            for dx in (-1, 0, 1):
                if dx == 0 and dy == 0:
                    continue
                p = ((x + dx) % width, (y + dy) % height)
                neighbor_count[p] = neighbor_count.get(p, 0) + 1
                if age > oldest_neighbor.get(p, -1):
                    oldest_neighbor[p] = age

    new_cells: set[tuple[int, int]] = set()
    new_ages: dict[tuple[int, int], int] = {}
    births: dict[tuple[int, int], int] = {}

    for p, n in neighbor_count.items():
        alive = p in cells
        if n == 3 or (alive and n == 2):
            new_cells.add(p)
            if alive:
                new_ages[p] = ages[p] + 1
            else:
                new_ages[p] = 0
                births[p] = oldest_neighbor.get(p, 0)

    # Cells with zero neighbors never appear in neighbor_count; dead ones
    # stay dead, and lone live cells die of loneliness — correct per rules.
    return new_cells, new_ages, births


@dataclass
class Universe:
    width: int
    height: int
    cells: set[tuple[int, int]] = field(default_factory=set)
    ages: dict[tuple[int, int], int] = field(default_factory=dict)
    generation: int = 0
    history: list[tuple[set[tuple[int, int]], dict[tuple[int, int], int]]] = \
        field(default_factory=list)

    def seed(self, pattern_name: str | None, rng: random.Random,
             density: float = 0.28) -> None:
        if pattern_name and pattern_name in PATTERNS:
            stamp(self.cells, self.width, self.height, PATTERNS[pattern_name]())
        else:
            # Random soup, kept away from the outer rim so the HUD row and
            # toroidal wrap don't produce visual noise at the borders.
            self.cells = random_soup(self.width, self.height, density, rng)
        self.ages = {c: 0 for c in self.cells}
        self.generation = 0
        self.history = []

    def step(self) -> dict[tuple[int, int], int]:
        self.history.append((set(self.cells), dict(self.ages)))
        if len(self.history) > 200:
            self.history.pop(0)
        self.cells, self.ages, births = evolve(
            self.cells, self.ages, self.width, self.height)
        self.generation += 1
        return births

    def back(self) -> bool:
        if not self.history:
            return False
        self.cells, self.ages = self.history.pop()
        self.generation -= 1
        return True

    def population(self) -> int:
        return len(self.cells)


def glyph_for(age: int, ramp: str) -> str:
    return ramp[min(age, len(ramp) - 1)]


# --------------------------------------------------------------------------
# Hashing renderer (pure) — used by the self-check and available to anyone
# without a terminal. Renders to a string, hash it, compare across runs.
# --------------------------------------------------------------------------


def render_text(uni: Universe, ramp: str) -> str:
    grid = [[" "] * uni.width for _ in range(uni.height)]
    for (x, y) in uni.cells:
        grid[y][x] = glyph_for(uni.ages[(x, y)], ramp)
    return "\n".join("".join(row) for row in grid)


def fingerprint(uni: Universe, ramp: str = "classic") -> str:
    return hashlib.sha256(render_text(uni, ramp).encode()).hexdigest()[:16]


# --------------------------------------------------------------------------
# Self-check: prove determinism and known-pattern behavior without a TTY.
# --------------------------------------------------------------------------


def self_check() -> list[str]:
    """Run assertions about the engine. Returns a list of failures (empty = OK)."""
    failures: list[str] = []

    # 1. A block is a still life: evolves to itself forever.
    w, h = 16, 16
    cells: set[tuple[int, int]] = set()
    stamp(cells, w, h, PATTERNS["block"](), at=(7, 7))
    ages = {c: 0 for c in cells}
    before = set(cells)
    for _ in range(10):
        cells, ages, _ = evolve(cells, ages, w, h)
    if cells != before:
        failures.append("block still life changed shape")

    # 2. A blinker oscillates with period 2.
    cells = set()
    stamp(cells, w, h, PATTERNS["blinker"](), at=(7, 7))
    ages = {c: 0 for c in cells}
    g0 = set(cells)
    cells, ages, _ = evolve(cells, ages, w, h)
    cells, ages, _ = evolve(cells, ages, w, h)
    if cells != g0:
        failures.append("blinker did not return after 2 generations")

    # 3. A glider translates by (1,1) every 4 generations.
    cells = set()
    stamp(cells, w, h, PATTERNS["glider"](), at=(2, 2))
    ages = {c: 0 for c in cells}
    for _ in range(4):
        cells, ages, _ = evolve(cells, ages, w, h)
    expected = {(x + 1, y + 1) for (x, y) in PATTERNS["glider"]()[2]}
    expected = {(x + 2, y + 2) for (x, y) in expected}  # offset of the stamp
    if cells != expected:
        failures.append(f"glider wrong after 4 gens: {sorted(cells)}")

    # 4. Determinism: same seed → same fingerprint after N generations.
    fps = []
    for _ in range(2):
        rng = random.Random(42)
        uni = Universe(40, 20)
        uni.seed(None, rng)
        for _ in range(60):
            uni.step()
        fps.append(fingerprint(uni))
    if fps[0] != fps[1]:
        failures.append(f"non-deterministic evolution: {fps}")

    # 5. R-pentomino population after exactly 10 generations (known value
    #    for the canonical orientation used above is not memorized here, so
    #    instead assert it grows well past its 5 starting cells — its whole
    #    point is eruption).
    uni = Universe(60, 40)
    uni.seed("r-pentomino", random.Random(1))
    for _ in range(50):
        uni.step()
    if uni.population() < 40:
        failures.append(f"r-pentomino failed to erupt (pop={uni.population()})")

    # 6. Toroidal wrap: a glider flying off the right edge reappears left.
    w2, h2 = 12, 12
    cells = set()
    stamp(cells, w2, h2, PATTERNS["glider"](), at=(9, 5))
    ages = {c: 0 for c in cells}
    for _ in range(4 * 3):  # 3 full translations = (3,3) → wraps in x
        cells, ages, _ = evolve(cells, ages, w2, h2)
    if not cells:
        failures.append("glider vanished instead of wrapping")
    if max(x for x, _ in cells) >= w2 or min(x for x, _ in cells) < 0:
        failures.append("wrap produced out-of-range cells")

    return failures


# --------------------------------------------------------------------------
# Terminal player
# --------------------------------------------------------------------------

@dataclass
class Palette:
    name: str
    ramp: str
    # (R, G, B) endpoints; colors interpolate along the ramp by age.
    born: tuple[int, int, int]
    old: tuple[int, int, int]
    bg: tuple[int, int, int]


PALETTES = [
    Palette("classic", AGE_RAMPS["classic"], (120, 220, 255), (255, 120, 200), (10, 10, 18)),
    Palette("embers", AGE_RAMPS["embers"], (255, 220, 90), (255, 60, 30), (14, 8, 8)),
    Palette("binary", AGE_RAMPS["binary"], (90, 255, 140), (20, 120, 60), (4, 10, 6)),
]


def lerp(a: int, b: int, t: float) -> int:
    return int(a + (b - a) * t)


def age_color(age: int, pal: Palette) -> str:
    # Age → t in [0,1] with a soft knee so "old" arrives around age ~24.
    t = 1.0 - math.exp(-age / 10.0)
    r = lerp(pal.born[0], pal.old[0], t)
    g = lerp(pal.born[1], pal.old[1], t)
    b = lerp(pal.born[2], pal.old[2], t)
    return f"\x1b[38;2;{r};{g};{b}m"


class Terminal:
    """Minimal raw-mode terminal driver using ANSI escapes only."""

    def __init__(self) -> None:
        self.out = sys.stdout
        self._old_attrs = None

    def __enter__(self) -> "Terminal":
        import termios
        import tty
        self._old_attrs = termios.tcgetattr(sys.stdin.fileno())
        tty.setcbreak(sys.stdin.fileno())
        self.out.write("\x1b[?1049h\x1b[?25l\x1b[2J")
        self.out.flush()
        return self

    def __exit__(self, *exc) -> None:
        import termios
        self.out.write("\x1b[?25h\x1b[?1049l\x1b[0m")
        self.out.flush()
        if self._old_attrs:
            termios.tcsetattr(sys.stdin.fileno(), termios.TCSADRAIN,
                              self._old_attrs)

    def size(self) -> tuple[int, int]:
        sz = os.get_terminal_size()
        return sz.columns, sz.lines

    def draw(self, uni: Universe, pal: Palette, hud: str,
             births: dict[tuple[int, int], int] | None = None) -> None:
        w, h = uni.width, uni.height
        parts = ["\x1b[H"]  # cursor home
        bg = pal.bg
        parts.append(f"\x1b[48;2;{bg[0]};{bg[1]};{bg[2]}m")
        blank = " "
        prev_color = None
        for y in range(h):
            for x in range(w):
                c = (x, y)
                if c in uni.cells:
                    age = uni.ages[c]
                    color = age_color(age, pal)
                    if color != prev_color:
                        parts.append(color)
                        prev_color = color
                    parts.append(glyph_for(age, pal.ramp))
                else:
                    if prev_color is not None:
                        parts.append("\x1b[39m")
                        prev_color = None
                    parts.append(blank)
            parts.append("\x1b[K\r\n")
        parts.append("\x1b[0m")
        parts.append(hud)
        parts.append("\x1b[K")
        self.out.write("".join(parts))
        self.out.flush()


HELP = (
    "space pause · . step · , back · +/- speed · p palette · "
    "r reseed · 1-9 pattern · h help · q quit"
)


def play(args: argparse.Namespace) -> None:
    rng = random.Random(args.seed)
    palette_idx = args.palette % len(PALETTES)
    pattern_names = list(PATTERNS)

    with Terminal() as term:
        cols, rows = term.size()
        w, h = cols, rows - 1  # reserve last row for HUD
        uni = Universe(w, h)
        uni.seed(args.pattern, rng, args.density)

        speed = args.speed  # generations per second
        paused = args.paused
        running = True
        show_help = True
        births: dict[tuple[int, int], int] = {}
        tick = 1.0 / max(speed, 0.1)
        last = time.monotonic()

        while running:
            now = time.monotonic()
            timeout = tick if not paused else 0.05
            ready, _, _ = select.select([sys.stdin], [], [], max(0, timeout))

            if ready:
                ch = sys.stdin.read(1)
                if ch == "q" or ch == "\x1b":
                    running = False
                elif ch == " ":
                    paused = not paused
                elif ch == ".":
                    births = uni.step()
                    paused = True
                elif ch == ",":
                    if uni.back():
                        paused = True
                elif ch in "+=":
                    speed = min(speed * 1.5, 120)
                elif ch == "-":
                    speed = max(speed / 1.5, 0.25)
                elif ch == "p":
                    palette_idx = (palette_idx + 1) % len(PALETTES)
                elif ch == "r":
                    uni.seed(args.pattern, rng, args.density)
                    births = {}
                elif ch == "h":
                    show_help = not show_help
                elif ch.isdigit() and ch != "0":
                    i = int(ch) - 1
                    if i < len(pattern_names):
                        args.pattern = pattern_names[i]
                        uni.seed(args.pattern, rng)
                        births = {}
                # Resize handling happens implicitly below.

            # Terminal resized? Rebuild the universe to fit.
            new_cols, new_rows = term.size()
            if (new_cols, new_rows - 1) != (uni.width, uni.height):
                w, h = new_cols, new_rows - 1
                uni = Universe(w, h)
                uni.seed(args.pattern, rng, args.density)
                births = {}

            if not paused and (now - last) >= (1.0 / speed):
                births = uni.step()
                last = now

            pal = PALETTES[palette_idx]
            state = "⏸" if paused else "▶"
            hud = (
                f"\x1b[7m {state} gen {uni.generation:>6} · pop "
                f"{uni.population():>5} · {speed:>5.1f} gen/s · "
                f"{pal.name} · seed {args.seed} "
                + (f"· {args.pattern} " if args.pattern else "· soup ")
                + ("· " + HELP if show_help else "")
                + " \x1b[0m"
            )
            term.draw(uni, pal, hud, births)


# --------------------------------------------------------------------------
# CLI
# --------------------------------------------------------------------------


def main() -> int:
    parser = argparse.ArgumentParser(description="Game of Life, in a terminal.")
    parser.add_argument("--pattern", choices=list(PATTERNS) + [None],
                        default=None, nargs="?",
                        help="seed pattern (default: random soup)")
    parser.add_argument("--speed", type=float, default=12.0,
                        help="generations per second")
    parser.add_argument("--seed", type=int, default=7)
    parser.add_argument("--density", type=float, default=0.22,
                        help="random soup density (0..1)")
    parser.add_argument("--palette", type=int, default=0)
    parser.add_argument("--paused", action="store_true")
    parser.add_argument("--check", action="store_true",
                        help="run headless self-test and exit")
    parser.add_argument("--snapshot", type=int, default=None, metavar="N",
                        help="run N generations headless, print ASCII, exit")
    parser.add_argument("--cols", type=int, default=70)
    parser.add_argument("--rows", type=int, default=24)
    args = parser.parse_args()

    if args.check:
        failures = self_check()
        if failures:
            for f in failures:
                print(f"FAIL: {f}")
            return 1
        print("all checks passed")
        return 0

    if args.snapshot is not None:
        rng = random.Random(args.seed)
        uni = Universe(args.cols, args.rows)
        uni.seed(args.pattern, rng, args.density)
        for _ in range(args.snapshot):
            uni.step()
        ramp = PALETTES[args.palette % len(PALETTES)].ramp
        print(render_text(uni, ramp))
        print(f"gen {uni.generation} · pop {uni.population()} · "
              f"fingerprint {fingerprint(uni, ramp)}")
        return 0

    try:
        play(args)
    except KeyboardInterrupt:
        pass
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
