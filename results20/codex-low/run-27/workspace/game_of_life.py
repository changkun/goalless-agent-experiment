#!/usr/bin/env python3
"""Terminal Conway's Game of Life with a Gosper glider gun and editing controls."""

import math
import os
import random
import sys
import termios
import time
import tty

try:
    import shutil
    COLS, ROWS = shutil.get_terminal_size((80, 24))
except Exception:
    COLS, ROWS = 80, 24

FIELD_W = 40
FIELD_H = 16
OFFSET_X = (COLS - FIELD_W) // 2
OFFSET_Y = (ROWS - FIELD_H) // 2


GLIDER_GUN = [
    (1, 5), (1, 6), (2, 5), (2, 6),
    (11, 5), (11, 6), (11, 7), (12, 4), (12, 8),
    (13, 3), (13, 9), (14, 3), (14, 9),
    (15, 6), (16, 4), (16, 8), (17, 5), (17, 6), (17, 7),
    (18, 6),
    (21, 3), (21, 4), (22, 3), (22, 4),
    (35, 1), (35, 2), (36, 1), (36, 2),
]


def read_key():
    """Read a single keypress without requiring Enter."""
    fd = sys.stdin.fileno()
    old = termios.tcgetattr(fd)
    try:
        tty.setcbreak(fd)
        ch = sys.stdin.read(1)
        if ch == "\x1b":
            extra = sys.stdin.read(2)
            return f"\x1b{extra}"
        return ch
    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, old)


class Board:
    def __init__(self, w, h):
        self.w = w
        self.h = h
        self.cells = set()

    def seed(self, coords):
        self.cells = {(x, y) for x, y in coords}

    def random(self, p=0.2):
        self.cells = {
            (x, y)
            for y in range(self.h)
            for x in range(self.w)
            if random.random() < p
        }

    def neighbors(self, px, py):
        n = 0
        for dy in (-1, 0, 1):
            for dx in (-1, 0, 1):
                if dx == 0 and dy == 0:
                    continue
                if (px + dx, py + dy) in self.cells:
                    n += 1
        return n

    def step(self):
        counts = {}
        for x, y in self.cells:
            for dy in (-1, 0, 1):
                for dx in (-1, 0, 1):
                    if dx == 0 and dy == 0:
                        continue
                    key = (x + dx, y + dy)
                    counts[key] = counts.get(key, 0) + 1
        new = set()
        for (x, y), n in counts.items():
            if n == 3 or (n == 2 and (x, y) in self.cells):
                new.add((x, y))
        self.cells = new

    def at(self, x, y):
        return (x, y) in self.cells

    def toggle(self, x, y):
        p = (x, y)
        if p in self.cells:
            self.cells.remove(p)
        else:
            self.cells.add(p)


def draw(board):
    sys.stdout.write("\x1b[?25l\x1b[2J\x1b[H")
    # Draw field border
    for i in range(FIELD_W + 2):
        sys.stdout.write(f"\x1b[{OFFSET_Y};{OFFSET_X + 1 + i}H#")
        sys.stdout.write(f"\x1b[{OFFSET_Y + FIELD_H + 1};{OFFSET_X + 1 + i}H#")
    for j in range(FIELD_H + 2):
        sys.stdout.write(f"\x1b[{OFFSET_Y + 1 + j};{OFFSET_X}H#")
        sys.stdout.write(f"\x1b[{OFFSET_Y + 1 + j};{OFFSET_X + FIELD_W + 1}H#")

    for x in range(FIELD_W):
        for y in range(FIELD_H):
            ch = "\u2588" if board.at(x, y) else " "
            sys.stdout.write(f"\x1b[{OFFSET_Y + 1 + y};{OFFSET_X + 1 + x}H{ch}")

    alive = len(board.cells)
    title = "CONWAY'S GAME OF LIFE"
    sys.stdout.write(f"\x1b[{OFFSET_Y - 2};{OFFSET_X}H{title}")
    info = f"Alive: {alive:<4} Generation: {generation}"
    sys.stdout.write(f"\x1b[{OFFSET_Y - 1};{OFFSET_X}H{info}")
    help_bar = (
        "space=pause  r=random  c=clear  q=quit  "
        "arrows=move  +/- = speed"
    )
    sys.stdout.write(f"\x1b[{ROWS};1H{help_bar}")
    sys.stdout.write(f"\x1b[{OFFSET_Y + FIELD_H + 2};{OFFSET_X}H")
    sys.stdout.flush()


generation = 0
running = True
paused = False
speed = 0.12


def parse_arrow(key):
    return {
        "\x1b[A": (0, -1),
        "\x1b[B": (0, 1),
        "\x1b[C": (1, 0),
        "\x1b[D": (-1, 0),
    }.get(key)


def main():
    global running, paused, speed, generation
    board = Board(FIELD_W, FIELD_H)
    board.seed(GLIDER_GUN)
    draw(board)

    cursor_x = FIELD_W // 2
    cursor_y = FIELD_H // 2
    last_step = time.time()

    try:
        while running:
            now = time.time()
            if not paused and now - last_step >= speed:
                board.step()
                generation += 1
                last_step = now
                draw(board)
                sys.stdout.write(
                    f"\x1b[{OFFSET_Y + 1 + cursor_y};{OFFSET_X + 1 + cursor_x}H\u2592"
                )
                sys.stdout.flush()

            if select(sys.stdin, [], [], 0)[0]:
                key = read_key()
                if key == "q":
                    running = False
                elif key == " ":
                    paused = not paused
                elif key == "r":
                    board.random()
                    generation = 0
                    draw(board)
                elif key == "c":
                    board.cells.clear()
                    generation = 0
                    draw(board)
                elif key == "+" or key == "=":
                    speed = max(0.02, speed - 0.02)
                elif key == "-" or key == "_":
                    speed = min(1.0, speed + 0.02)
                else:
                    d = parse_arrow(key)
                    if d:
                        dx, dy = d
                        cursor_x = (cursor_x + dx) % FIELD_W
                        cursor_y = (cursor_y + dy) % FIELD_H
                draw(board)
                sys.stdout.write(
                    f"\x1b[{OFFSET_Y + 1 + cursor_y};{OFFSET_X + 1 + cursor_x}H\u2592"
                )
                sys.stdout.flush()
            else:
                time.sleep(0.01)
    except KeyboardInterrupt:
        pass
    finally:
        sys.stdout.write("\x1b[?25h\x1b[2J\x1b[H")
        sys.stdout.flush()


def select(r, w, x, timeout):
    import select as sel
    return sel.select(r, w, x, timeout)


if __name__ == "__main__":
    main()
