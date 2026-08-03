#!/usr/bin/env python3
"""Conway's Game of Life in the terminal.

A small, dependency-free cell automaton using only Python's stdlib `curses`.

Controls
--------
  arrows / h j k l   move cursor
  space              toggle cell under cursor (edit mode)
  p                  place the current preset pattern
  [ ]                cycle through edition modes / presets
  s                  toggle simulation (run / pause)
  +/-                simulation speed
  c                  clear the board
  r                  random fill
  n                  single-step (advance one generation while paused)
  q                  quit

Usage
-----
  python3 life.py
"""

import argparse
import curses
import random
import sys
import time

# Tunable preset universe dimensions. The board wraps around (toroidal).
WIDTH = 96
HEIGHT = 44

# One generation, in seconds, at speed level 0. Higher speed = faster.
BASE_STEP = 0.30


def parse_args(argv):
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--width", type=int, default=WIDTH, help="universe width in cells")
    p.add_argument("--height", type=int, default=HEIGHT, help="universe height in cells")
    p.add_argument("--random", action="store_true", help="start with a random fill")
    return p.parse_args(argv)


# --------------------------------------------------------------------------- #
# Preset patterns. Each is a list of (row, col) offsets from a top-left anchor.
# --------------------------------------------------------------------------- #
PRESETS = {
    "glider":      [(0, 1), (1, 2), (2, 0), (2, 1), (2, 2)],
    "blinker":     [(0, 0), (0, 1), (0, 2)],
    "pulsar": [ (0, 2), (0, 3), (0, 4), (0, 8), (0, 9), (0, 10),
                (2, 0), (2, 5), (2, 7), (2, 12),
                (3, 0), (3, 5), (3, 7), (3, 12),
                (4, 0), (4, 5), (4, 7), (4, 12),
                (5, 2), (5, 3), (5, 4), (5, 8), (5, 9), (5, 10),
                (7, 2), (7, 3), (7, 4), (7, 8), (7, 9), (7, 10),
                (8, 0), (8, 5), (8, 7), (8, 12),
                (9, 0), (9, 5), (9, 7), (9, 12),
                (10, 0), (10, 5), (10, 7), (10, 12),
                (12, 2), (12, 3), (12, 4), (12, 8), (12, 9), (12, 10) ],
    "gosper": [  # Gosper glider gun
        (0, 24),
        (1, 22), (1, 24),
        (2, 12), (2, 13), (2, 20), (2, 21), (2, 34), (2, 35),
        (3, 11), (3, 15), (3, 20), (3, 21), (3, 34), (3, 35),
        (4, 0), (4, 1), (4, 10), (4, 16), (4, 20), (4, 21),
        (5, 0), (5, 1), (5, 10), (5, 14), (5, 16), (5, 17), (5, 22), (5, 24),
        (6, 10), (6, 16), (6, 24),
        (7, 11), (7, 15),
        (8, 12), (8, 13),
    ],
    "methuselah": [  # R-pentomino — small seed, chaotic long tail
        (0, 1), (0, 2), (1, 0), (1, 1), (2, 1),
    ],
    "block-laying switch engine": [
        (0, 5), (0, 6), (1, 5), (1, 7), (2, 5),
        (4, 2), (4, 3), (4, 4), (5, 2), (6, 3),
    ],
    "glider-duo": [
        (0, 1), (1, 2), (2, 0), (2, 1), (2, 2),
        (0, 10), (1, 11), (2, 9), (2, 10), (2, 11),
    ],
}


def step(world, width, height):
    """Advance `world` (dict of (r, c) -> True) by one generation."""
    counts = {}
    for (r, c) in world:
        for dr in (-1, 0, 1):
            for dc in (-1, 0, 1):
                if dr == 0 and dc == 0:
                    continue
                nr = (r + dr) % height
                nc = (c + dc) % width
                counts[(nr, nc)] = counts.get((nr, nc), 0) + 1

    new = {}
    for cell, n in counts.items():
        if n == 3 or (n == 2 and cell in world):
            new[cell] = True
    return new


def random_fill(width, height, p=0.22):
    return {(r, c): True
            for r in range(height) for c in range(width)
            if random.random() < p}


# --------------------------------------------------------------------------- #
# The app. A thin state machine around curses.
# --------------------------------------------------------------------------- #
class App:
    def __init__(self, width, height, start_random=False):
        self.width, self.height = width, height
        self.world = random_fill(width, height) if start_random else {}
        self.cursor = (height // 2, width // 2)
        self.running = False
        self.speed = 0
        self.preset_index = 0
        self.preset_names = list(PRESETS)
        self.tick = 0.0

    # -- pattern placement -------------------------------------------------- #
    def place_preset(self):
        name = self.preset_names[self.preset_index]
        r0, c0 = self.cursor
        for dr, dc in PRESETS[name]:
            self.world[(r0 + dr, c0 + dc)] = True

    # -- helpers ------------------------------------------------------------ #
    def toggle(self):
        if self.cursor in self.world:
            del self.world[self.cursor]
        else:
            self.world[self.cursor] = True

    def clear(self):
        self.world = {}

    def randomize(self):
        self.world = random_fill(self.width, self.height)

    # -- dispatch ----------------------------------------------------------- #
    def handle(self, key):
        r, c = self.cursor
        if key in (curses.KEY_UP, ord("k")):
            self.cursor = ((r - 1) % self.height, c)
        elif key in (curses.KEY_DOWN, ord("j")):
            self.cursor = ((r + 1) % self.height, c)
        elif key in (curses.KEY_LEFT, ord("h")):
            self.cursor = (r, (c - 1) % self.width)
        elif key in (curses.KEY_RIGHT, ord("l")):
            self.cursor = (r, (c + 1) % self.width)
        elif key == ord(" "):
            self.toggle()
        elif key == ord("p"):
            self.place_preset()
        elif key == ord("\t"):
            self.preset_index = (self.preset_index + 1) % len(self.preset_names)
        elif key == ord("s"):
            self.running = not self.running
        elif key in (ord("="), ord("+")):
            self.speed = max(self.speed - 1, -4)
        elif key in (ord("-"), ord("_")):
            self.speed = min(self.speed + 1, 6)
        elif key == ord("c"):
            self.clear()
        elif key == ord("r"):
            self.randomize()
        elif key == ord("n"):
            self.world = step(self.world, self.width, self.height)
        elif key in (ord("q"), 27):  # q or Esc
            return False
        return True

    def step_interval(self):
        return BASE_STEP * (2 ** self.speed)  # each higher speed doubles the rate


def draw(stdscr, app):
    stdscr.erase()
    if curses.has_colors():
        dim = curses.color_pair(1)
        accent = curses.color_pair(2)
    else:
        dim = curses.A_DIM
        accent = curses.A_BOLD

    for (r, c) in app.world:
        try:
            stdscr.addch(r + 1, c + 1, "#", accent)
        except curses.error:
            pass  # off-screen; ignore

    # cursor marker
    r, c = app.cursor
    ch = "@" if (r, c) in app.world else "."
    try:
        stdscr.addch(r + 1, c + 1, ch, dim)
    except curses.error:
        pass

    # status bar
    alive = len(app.world)
    state = "RUN " if app.running else "PAUSED"
    preset = app.preset_names[app.preset_index]
    status = (
        f" {state}  gen cells:{alive:6d}  speed:{app.speed:+d}  "
        f"pattern:[{preset}] (Tab)  space:draw  p:place  "
        f"s:run  n:step  c:clear  r:random  q:quit "
    )
    try:
        stdscr.addnstr(app.height + 1, 0, " " * app.width, app.width)
        stdscr.addnstr(app.height + 1, 0, status, stdscr.getmaxyx()[1] - 1, dim)
        stdscr.move(r + 1, c + 1)
    except curses.error:
        pass


def main(stdscr, width, height, start_random):
    curses.curs_set(0)
    stdscr.nodelay(True)
    stdscr.keypad(True)
    if curses.has_colors():
        curses.start_color()
        curses.init_pair(1, curses.COLOR_WHITE, curses.COLOR_BLACK)
        curses.init_pair(2, curses.COLOR_GREEN, curses.COLOR_BLACK)

    app = App(width, height, start_random)
    last_step = time.monotonic()

    while True:
        key = stdscr.getch()
        if key != -1:
            if not app.handle(key):
                break

        # Autostep only while running; throttle by speed.
        if app.running:
            now = time.monotonic()
            while now - last_step >= app.step_interval():
                app.world = step(app.world, app.width, app.height)
                last_step += app.step_interval()
                now = time.monotonic()

        draw(stdscr, app)
        stdscr.refresh()
        time.sleep(0.015)


if __name__ == "__main__":
    args = parse_args(sys.argv[1:])
    curses.wrapper(lambda s: main(s, args.width, args.height, args.random))
