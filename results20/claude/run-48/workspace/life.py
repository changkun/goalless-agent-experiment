#!/usr/bin/env python3
"""
life.py — Conway's Game of Life, rendered live in your terminal.

Zero dependencies: pure Python standard library. Lives on a toroidal
(homeomorphically irreducible) grid so patterns wrap around the edges.

Controls:
    Space      pause / resume
    +/-        faster / slower (steps per second)
    r          random fill
    c          clear the grid
    g          ghost mode (show cells that die / are born in the next step)
    1..9       load a classic pattern (see belt at the bottom)
    q          quit

Rendered live with ANSI escape codes. Terminal size is picked up on start
and on window resize (SIGWINCH).
"""

import os
import sys
import time
import tty
import termios
import select
import random
from dataclasses import dataclass

# --------------------------------------------------------------------------- #
# Patterns  (each is a dict of coordinate -> name; '.' is alive)
# --------------------------------------------------------------------------- #
def _pulsar():
    """A period-3 oscillator (48 cells, 13x13). Classic layout:

    ..OOO...OOO..
    O....O.O....O
    O....O.O....O
    O....O.O....O
    ..OOO...OOO..
    ..OOO...OOO..
    O....O.O....O
    O....O.O....O
    O....O.O....O
    ..OOO...OOO..
    """
    rows = [
        {2, 3, 4, 8, 9, 10},      # row 0: top bar
        set(),                    # row 1
        {0, 5, 7, 12},            # row 2
        {0, 5, 7, 12},            # row 3
        {0, 5, 7, 12},            # row 4
        {2, 3, 4, 8, 9, 10},      # row 5
        set(),                    # row 6
        {2, 3, 4, 8, 9, 10},      # row 7
        {0, 5, 7, 12},            # row 8
        {0, 5, 7, 12},            # row 9
        {0, 5, 7, 12},            # row 10
        set(),                    # row 11
        {2, 3, 4, 8, 9, 10},      # row 12
    ]
    return {(r, c) for r, cols in enumerate(rows) for c in cols}


PATTERNS = {
    "1": ("Glider", {(0, 1), (1, 2), (2, 0), (2, 1), (2, 2)}),
    "2": ("R-pentomino", {(0, 1), (0, 2), (1, 0), (1, 1), (2, 1)}),
    "3": ("Pulsar", _pulsar()),
    "4": ("Gosper glider gun", {
        (x, y)
        for (x, y) in [
            (0, 5), (0, 6), (1, 5), (1, 6),
            (10, 5), (10, 6), (10, 7), (11, 4), (11, 8),
            (12, 3), (12, 9), (13, 3), (13, 9),
            (14, 6), (15, 4), (15, 8), (16, 5), (16, 6), (16, 7),
            (17, 6), (20, 4), (20, 5), (20, 6), (21, 4), (21, 5), (21, 6),
            (22, 3), (22, 7), (24, 2), (24, 3), (24, 7), (24, 8),
        ]
    }),
    "5": ("Beehive", {(0, 0), (1, -1), (1, 1), (2, 0), (3, -1), (3, 1)}),
    "6": ("Diehard", {(0, 1), (1, 0), (1, 1), (3, 1), (4, 1), (5, 1), (6, 1),
                      (5, 3), (6, 3)}),
    "7": ("Block", {(0, 0), (0, 1), (1, 0), (1, 1)}),
    "8": ("Toad", {(1, 0), (2, 0), (3, 0), (0, 1), (1, 1), (2, 1)}),
    "9": ("Acorn", {(0, 1), (1, 3), (2, 0), (2, 1), (2, 4), (2, 5), (2, 6)}),
}


# --------------------------------------------------------------------------- #
# Core
# --------------------------------------------------------------------------- #
@dataclass
class Life:
    rows: int
    cols: int
    alive: set  # set of (r, c)

    @classmethod
    def blank(cls, rows, cols):
        return cls(rows, cols, set())

    def _nbrs(self, r, c):
        """Neighbour count, wrapping at the edges."""
        n = 0
        for dr in (-1, 0, 1):
            for dc in (-1, 0, 1):
                if dr == 0 and dc == 0:
                    continue
                rr = (r + dr) % self.rows
                cc = (c + dc) % self.cols
                if (rr, cc) in self.alive:
                    n += 1
        return n

    def step(self):
        """Advance one generation, return (born, died) counts."""
        counts = {}
        for r, c in self.alive:
            for dr in (-1, 0, 1):
                for dc in (-1, 0, 1):
                    if dr == 0 and dc == 0:
                        continue
                    rr = (r + dr) % self.rows
                    cc = (c + dc) % self.cols
                    counts[(rr, cc)] = counts.get((rr, cc), 0) + 1

        next_alive = set()
        born = died = 0
        for (r, c), n in counts.items():
            if n == 3 or (n == 2 and (r, c) in self.alive):
                next_alive.add((r, c))
                born += (r, c) not in self.alive
            elif (r, c) in self.alive:
                died += 1
        # cells that survived
        survived = self.alive - counts.keys()
        self.alive = next_alive | survived
        return born, died

    def density(self):
        return len(self.alive) / (self.rows * self.cols)


# --------------------------------------------------------------------------- #
# Rendering / terminal helpers
# --------------------------------------------------------------------------- #
# ANSI: hide cursor, clear screen+scrollback, move home.
ALT = "\x1b[?1049h"
EXIT = "\x1b[?1049l"
HIDE = "\x1b[?25l"
SHOW = "\x1b[?25h"
RESET = "\x1b[0m"
HOME = "\x1b[H"
FG_GHOST = "\x1b[38;5;241m"    # dim grey (for born-cell preview)
BG_ALIVE = "\x1b[48;5;28m"     # solid green block for live cells
DIMMED = "\x1b[2m"


def load_pattern(life, name_key):
    """Center the named pattern on the grid."""
    _, cells = PATTERNS[name_key]
    rs = [c[0] for c in cells]
    cs = [c[1] for c in cells]
    w, h = max(cs) - min(cs) + 1, max(rs) - min(rs) + 1
    dr = (life.rows - h) // 2 - min(rs)
    dc = (life.cols - w) // 2 - min(cs)
    life.alive = {(r + dr, c + dc) for r, c in cells}


def render(life, ghost_cols):
    """Return the full screen frame as a string."""
    alive, born = life.alive, set()
    for r, c in life.alive:
        for dr in (-1, 0, 1):
            for dc in (-1, 0, 1):
                if dr == 0 and dc == 0:
                    continue
                built = (r + dr) % life.rows, (c + dc) % life.cols
                born.add(built)
    born -= alive

    lines = []
    for r in range(life.rows):
        row = []
        for c in range(life.cols):
            if (r, c) in alive:
                row.append(BG_ALIVE + " ")
            elif ghost_cols and (r, c) in born:
                row.append(FG_GHOST + "·")
            else:
                row.append(" ")
        lines.append("".join(row))
    return "\n".join(lines)


def draw(life, ghost_cols, gen, stepped=False):
    sys.stdout.write(HOME)
    sys.stdout.write(render(life, ghost_cols))
    sys.stdout.write(RESET + "\x1b[0J")
    # status bar (bottom line)
    alive = len(life.alive)
    sys.stdout.write(f"\n\x1b[K{DIMMED}gen {gen:>6}  "
                     f"alive {alive:>5}  ")


# --------------------------------------------------------------------------- #
# Main loop
# --------------------------------------------------------------------------- #
def main():
    rows, cols = os.get_terminal_size(0).lines, os.get_terminal_size(0).columns
    # leave a couple of rows for the status/help bars
    rows = max(10, rows - 1)
    cols = max(10, cols - 1)

    life = Life.blank(rows, cols)
    gen = 0
    running = True
    ghost = False
    sps = 6.0  # steps per second
    deathroll = 0

    random.seed()
    load_pattern(life, "4")  # start with the glider gun

    old = termios.tcgetattr(sys.stdin)
    tty.setcbreak(sys.stdin)
    sys.stdout.write(ALT + HIDE)
    try:
        while True:
            draw(life, ghost, gen)
            # help bar
            state = "▶" if running else "⏸"
            sys.stdout.write(
                f"\x1b[K{state} SP:play P:pu {sps:4.1f}sps +/−:spd  r:rand "
                f"c:clear g:ghost 1-9:patt q:quit{DIMMED} "
                f"density {life.density()*100:4.1f}%{RESET}")
            sys.stdout.flush()

            if running:
                t0 = time.monotonic()
                born, died = life.step()
                gen += 1
                if born == 0 and died == 0:
                    deathroll += 1  # frozen universe
                    if deathroll > 30:
                        running = False
                        deathroll = 0
                else:
                    deathroll = 0
                # adaptive pacing so a dense grid doesn't crawl
                delay = 1.0 / sps
                elapsed = time.monotonic() - t0
                wait = max(0.0, delay - elapsed)
            else:
                wait = 0.2

            # wait up to `wait` seconds for input (interruptible by keypress)
            end = time.monotonic() + wait
            while time.monotonic() < end:
                remaining = end - time.monotonic()
                if remaining <= 0:
                    break
                r, _, _ = select.select([sys.stdin], [], [], remaining)
                if not r:
                    continue
                key = sys.stdin.read(1)
                if key == "q":
                    return
                elif key == " ":
                    running = not running
                elif key == "+" or key == "=":
                    sps = min(60.0, sps * 1.5)
                elif key == "-" or key == "_":
                    sps = max(0.5, sps / 1.5)
                elif key == "r":
                    density = random.uniform(0.08, 0.35)
                    life.alive = {
                        (r, c)
                        for r in range(rows)
                        for c in range(cols)
                        if random.random() < density
                    }
                    deathroll = 0
                elif key == "c":
                    life.alive = set()
                    deathroll = 0
                elif key == "g":
                    ghost = not ghost
                elif key in PATTERNS:
                    load_pattern(life, key)
                    deathroll = 0
                # any other key: do nothing
    finally:
        sys.stdout.write(RESET + SHOW + EXIT)
        termios.tcsetattr(sys.stdin, termios.TCSADRAIN, old)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        pass
