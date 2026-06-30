#!/usr/bin/env python3
"""
Conway's Game of Life — terminal renderer with curated starting patterns.
Usage: python life.py [pattern] [--delay SECONDS]
Patterns: glider, pulsar, gosper, acorn, rpentomino, random
"""

import sys
import time
import os
import math
import random
import argparse

# Terminal control
def clear():
    os.write(1, b"\033[2J\033[H")

def hide_cursor():
    os.write(1, b"\033[?25l")

def show_cursor():
    os.write(1, b"\033[?25h")

def move_home():
    os.write(1, b"\033[H")

def color(r, g, b):
    return f"\033[38;2;{r};{g};{b}m"

RESET = "\033[0m"


def terminal_size():
    import shutil
    sz = shutil.get_terminal_size((80, 24))
    return sz.columns, sz.lines


class Grid:
    def __init__(self, w, h):
        self.w = w
        self.h = h
        self.cells = set()
        self.gen = 0

    def set(self, x, y):
        self.cells.add((x % self.w, y % self.h))

    def place_pattern(self, pattern, ox=0, oy=0):
        for (x, y) in pattern:
            self.set(x + ox, y + oy)

    def step(self):
        neighbor_counts = {}
        for (x, y) in self.cells:
            for dx in (-1, 0, 1):
                for dy in (-1, 0, 1):
                    if dx == 0 and dy == 0:
                        continue
                    nb = ((x + dx) % self.w, (y + dy) % self.h)
                    neighbor_counts[nb] = neighbor_counts.get(nb, 0) + 1

        next_cells = set()
        for cell, count in neighbor_counts.items():
            if count == 3 or (count == 2 and cell in self.cells):
                next_cells.add(cell)

        self.cells = next_cells
        self.gen += 1

    def population(self):
        return len(self.cells)

    def render(self):
        # Color shifts gently through hues based on generation
        t = self.gen * 0.04
        r = int(127 + 127 * abs((t % 3) - 1.5) / 1.5 * (1 if (t % 6) < 3 else -1))
        r = max(80, min(255, int(128 + 100 * (0.5 + 0.5 * math.sin(t)))))
        g = max(80, min(255, int(128 + 100 * (0.5 + 0.5 * math.sin(t + 2.094)))))
        b = max(80, min(255, int(128 + 100 * (0.5 + 0.5 * math.sin(t + 4.189)))))

        cell_char = color(r, g, b) + "██" + RESET
        empty_char = "  "

        rows = []
        for y in range(self.h):
            row = []
            for x in range(self.w):
                row.append(cell_char if (x, y) in self.cells else empty_char)
            rows.append("".join(row))

        status = (
            f"{color(200,200,200)}Gen {self.gen:6d} | "
            f"Pop {self.population():6d} | "
            f"[q] quit  [r] reset{RESET}"
        )
        return "\n".join(rows) + "\n" + status


# ── Patterns ──────────────────────────────────────────────────────────────────

PATTERNS = {}

def pattern(name):
    def decorator(fn):
        PATTERNS[name] = fn
        return fn
    return decorator

@pattern("glider")
def make_glider(w, h):
    g = Grid(w, h)
    # Four gliders heading different directions
    glider = [(1,0),(2,1),(0,2),(1,2),(2,2)]
    g.place_pattern(glider, 5, 5)
    glider_h = [(x, y) for (x,y) in [(1,0),(2,1),(0,2),(1,2),(2,2)]]
    # flip horizontally
    glider2 = [(2-x, y) for (x,y) in glider]
    g.place_pattern(glider2, w-10, 5)
    # flip vertically
    glider3 = [(x, 2-y) for (x,y) in glider]
    g.place_pattern(glider3, 5, h-10)
    glider4 = [(2-x, 2-y) for (x,y) in glider]
    g.place_pattern(glider4, w-10, h-10)
    return g

@pattern("gosper")
def make_gosper(w, h):
    # Gosper Glider Gun
    g = Grid(w, h)
    gun = [
        (24,0),
        (22,1),(24,1),
        (12,2),(13,2),(20,2),(21,2),(34,2),(35,2),
        (11,3),(15,3),(20,3),(21,3),(34,3),(35,3),
        (0,4),(1,4),(10,4),(16,4),(20,4),(21,4),
        (0,5),(1,5),(10,5),(14,5),(16,5),(17,5),(22,5),(24,5),
        (10,6),(16,6),(24,6),
        (11,7),(15,7),
        (12,8),(13,8),
    ]
    ox = max(0, (w - 36) // 2)
    oy = max(0, (h - 10) // 2)
    g.place_pattern(gun, ox, oy)
    return g

@pattern("pulsar")
def make_pulsar(w, h):
    g = Grid(w, h)
    # Pulsar — period 3 oscillator
    pulsar = [
        (2,0),(3,0),(4,0),(8,0),(9,0),(10,0),
        (0,2),(5,2),(7,2),(12,2),
        (0,3),(5,3),(7,3),(12,3),
        (0,4),(5,4),(7,4),(12,4),
        (2,5),(3,5),(4,5),(8,5),(9,5),(10,5),
        (2,7),(3,7),(4,7),(8,7),(9,7),(10,7),
        (0,8),(5,8),(7,8),(12,8),
        (0,9),(5,9),(7,9),(12,9),
        (0,10),(5,10),(7,10),(12,10),
        (2,12),(3,12),(4,12),(8,12),(9,12),(10,12),
    ]
    ox = (w - 13) // 2
    oy = (h - 13) // 2
    g.place_pattern(pulsar, ox, oy)
    return g

@pattern("acorn")
def make_acorn(w, h):
    g = Grid(w, h)
    # Acorn — tiny pattern that explodes after ~5200 generations
    acorn = [(0,1),(1,3),(2,0),(2,1),(4,1),(5,1),(6,1)]
    ox = w // 2 - 3
    oy = h // 2 - 1
    g.place_pattern(acorn, ox, oy)
    return g

@pattern("rpentomino")
def make_rpentomino(w, h):
    g = Grid(w, h)
    # R-pentomino — stabilizes after 1103 generations
    rp = [(1,0),(2,0),(0,1),(1,1),(1,2)]
    ox = w // 2 - 1
    oy = h // 2 - 1
    g.place_pattern(rp, ox, oy)
    return g

@pattern("random")
def make_random(w, h):
    g = Grid(w, h)
    density = 0.3
    for y in range(h):
        for x in range(w):
            if random.random() < density:
                g.set(x, y)
    return g


# ── Main loop ─────────────────────────────────────────────────────────────────

def setup_stdin_nonblocking():
    import tty, termios
    fd = sys.stdin.fileno()
    old = termios.tcgetattr(fd)
    tty.setraw(fd)
    import fcntl
    fl = fcntl.fcntl(fd, fcntl.F_GETFL)
    fcntl.fcntl(fd, fcntl.F_SETFL, fl | os.O_NONBLOCK)
    return old, fd

def restore_stdin(old, fd):
    import termios
    termios.tcsetattr(fd, termios.TCSADRAIN, old)

def read_key():
    try:
        return sys.stdin.read(1)
    except (BlockingIOError, IOError):
        return None


def run(pattern_name, delay):
    cols, rows = terminal_size()
    # Each cell is 2 chars wide, reserve 1 row for status
    w = cols // 2
    h = rows - 1

    grid = PATTERNS[pattern_name](w, h)

    old_settings, fd = setup_stdin_nonblocking()
    hide_cursor()
    clear()

    try:
        while True:
            key = read_key()
            if key in ("q", "Q", "\x03"):
                break
            if key in ("r", "R"):
                grid = PATTERNS[pattern_name](w, h)
                clear()

            frame = grid.render()
            move_home()
            sys.stdout.write(frame)
            sys.stdout.flush()

            grid.step()
            time.sleep(delay)
    finally:
        show_cursor()
        restore_stdin(old_settings, fd)
        clear()
        print(f"Ran {grid.gen} generations. Final population: {grid.population()}")


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("pattern", nargs="?", default="gosper",
                        choices=list(PATTERNS.keys()),
                        help=f"Starting pattern (default: gosper)")
    parser.add_argument("--delay", type=float, default=0.07,
                        help="Seconds between generations (default: 0.07)")
    parser.add_argument("--list", action="store_true", help="List available patterns")
    args = parser.parse_args()

    if args.list:
        print("Available patterns:")
        descriptions = {
            "glider": "Four gliders racing toward each other from the corners",
            "gosper": "Gosper Glider Gun — fires gliders endlessly",
            "pulsar": "Pulsar — a period-3 oscillator, one of the most beautiful",
            "acorn": "Acorn — tiny seed that takes ~5200 generations to stabilize",
            "rpentomino": "R-pentomino — stabilizes after 1103 generations",
            "random": "Random soup — 30% density, emergent chaos",
        }
        for name, desc in descriptions.items():
            print(f"  {name:12s}  {desc}")
        return

    run(args.pattern, args.delay)


if __name__ == "__main__":
    main()
