#!/usr/bin/env python3
"""Game of Life in the terminal.

Interactively run Conway's Game of Life using curses.

Controls:
  space        play / pause
  . or ,       step forward / back one generation (when paused)
  [ / ]        slower / faster
  g            glider gun
  p            pulsar
  r            random soup
  c            clear
  q            quit
"""
import argparse
import curses
import random
import time

from patterns import find

DEAD, ALIVE = ".", "#"  # cell glyphs (monospace fonts keep this aligned)

# Everything pattern-related lives in patterns.py; here we only map the UI
# shortcuts ("g" and "p") to the pattern keys that module understands.
GLIDER_GUN = find("gosper_glider_gun")   # (pretty_name, cells)
PULSAR = find("pulsar")                  # (pretty_name, cells)
PATTERN_KEY = {"g": "gosper_glider_gun", "p": "pulsar"}


class Life:
    """Finite rectangular universe of Conway's Game of Life."""

    def __init__(self, height, width):
        self.h = height
        self.w = width
        self.clear()

    def clear(self):
        self.cells = set()

    def cell(self, y, x):
        return (y % self.h, x % self.w) in self.cells

    def seed(self, cells):
        """Add cells, wrapping any that fall off the edges."""
        for y, x in cells:
            self.cells.add((y % self.h, x % self.w))

    def neighbors(self, y, x):
        """Live neighbor count for a wrapped toroidal position."""
        n = 0
        for dy in (-1, 0, 1):
            for dx in (-1, 0, 1):
                if dy == 0 and dx == 0:
                    continue
                if self.cell(y + dy, x + dx):
                    n += 1
        return n

    def step(self):
        """Advance one generation using the standard rules."""
        nxt = set()
        candidates = set()
        for y, x in self.cells:
            candidates.add((y, x))
            for dy in (-1, 0, 1):
                for dx in (-1, 0, 1):
                    candidates.add(((y + dy) % self.h, (x + dx) % self.w))
        for y, x in candidates:
            n = self.neighbors(y, x)
            live = (y, x) in self.cells
            if live and n in (2, 3):
                nxt.add((y, x))
            elif not live and n == 3:
                nxt.add((y, x))
        self.cells = nxt

    def count(self):
        return len(self.cells)


def draw(stdscr, life, gen, alive, msg):
    h, w = life.h, life.w
    max_y, max_x = stdscr.getmaxyx()
    # Center the universe if the terminal is larger than it.
    off_y = max(0, (max_y - h) // 2)
    off_x = max(0, (max_x - w) // 2)
    for y in range(h):
        row = "".join(ALIVE if (y, x) in life.cells else DEAD for x in range(w))
        col = min(max_x, off_x + w)
        try:
            stdscr.addstr(off_y + y, off_x, row[: max(0, max_x - off_x)][: col - off_x])
        except curses.error:
            pass
    bar = f" gen {gen} | alive {alive} | {msg}"
    try:
        stdscr.addstr(max_y - 1, 0, bar[: max_x])
    except curses.error:
        pass
    stdscr.refresh()


def main(stdscr, args):
    curses.curs_set(0)
    stdscr.nodelay(True)  # non-blocking getch
    stdscr.clear()

    max_y, max_x = stdscr.getmaxyx()
    h = max(10, min(args.height, max_y - 4))
    w = max(20, min(args.width, max_x - 2))
    life = Life(h, w)

    running = False
    gen = 0
    msg = "space=play  []=speed  g=gun  p=pulsar  r=random  c=clear  q=quit"
    speed = 0.2

    if args.pattern in PATTERN_KEY:
        name, cells = find(PATTERN_KEY[args.pattern])
        life.seed(cells)
        msg = f"{name} loaded — {msg}"
    else:
        life.seed(GLIDER_GUN[1])
        msg = f"{GLIDER_GUN[0]} loaded — {msg}"

    draw(stdscr, life, gen, life.count(), msg)

    while True:
        ch = stdscr.getch()
        if ch == ord("q"):
            break
        elif ch == ord(" "):
            running = not running
            msg = "running" if running else "paused"
        elif ch == ord("r"):
            running = False
            gen = 0
            for y in range(h):
                for x in range(w):
                    if random.random() < 0.28:
                        life.cells.add((y, x))
            msg = "random soup"
        elif ch == ord("c"):
            running = False
            gen = 0
            life.clear()
            msg = "cleared"
        elif ch in (ord("g"), ord("p")):
            running = False
            name, cells = find(PATTERN_KEY[chr(ch)])
            life.clear()
            life.seed(cells)
            msg = name
        elif ch == ord("]") or ch == ord("+"):
            speed = max(0.02, speed / 1.5)
            msg = f"faster ({speed:.2f}s)"
        elif ch == ord("[") or ch == ord("-"):
            speed = min(2.0, speed * 1.5)
            msg = f"slower ({speed:.2f}s)"
        elif ch == ord("."):
            running = False
            life.step()
            gen += 1
            msg = f"step {gen}"
        elif ch == ord(","):
            running = False
            gen = max(0, gen - 1)
            msg = "un-step (generation counter only)"

        if running:
            life.step()
            gen += 1
            time.sleep(speed)

        draw(stdscr, life, gen, life.count(), msg)


def run(stdscr, args):
    try:
        main(stdscr, args)
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--height", type=int, default=24)
    parser.add_argument("--width", type=int, default=70)
    parser.add_argument("--pattern", choices=("gosper_glider_gun", "pulsar"),
                        default="gosper_glider_gun")
    args = parser.parse_args()
    curses.wrapper(lambda s: run(s, args))
