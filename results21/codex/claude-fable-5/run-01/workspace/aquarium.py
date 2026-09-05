#!/usr/bin/env python3
"""A procedural ASCII aquarium.

Run it in a terminal and watch fish swim, bubbles rise, and seaweed sway.

Usage:
    python3 aquarium.py                 # run forever (Ctrl+C to quit)
    python3 aquarium.py --frames 100    # render a fixed number of frames
    python3 aquarium.py --fps 15        # change animation speed
"""

import argparse
import os
import random
import shutil
import signal
import sys
import time

RESET = "\x1b[0m"
HIDE_CURSOR = "\x1b[?25l"
SHOW_CURSOR = "\x1b[?25h"
CLEAR = "\x1b[2J"
HOME = "\x1b[H"

FISH_RIGHT = ["><>", "><((*>", ">=)o>", "><}}}*>", "}<(([o>"]
FISH_LEFT = ["<><", "<*))><", "<o(=<", "<*{{{><", "<o]))>{"]
FISH_COLORS = [196, 202, 208, 214, 220, 226, 118, 51, 45, 39, 201, 213]
WATER_COLOR = 24
SAND_COLOR = 179
WEED_COLOR = 34
BUBBLE_COLOR = 117


def color(code):
    return f"\x1b[38;5;{code}m"


class Fish:
    def __init__(self, width, height):
        self.width = width
        self.height = height
        self.respawn(initial=True)

    def respawn(self, initial=False):
        self.direction = random.choice((-1, 1))
        art = random.choice(FISH_RIGHT if self.direction > 0 else FISH_LEFT)
        self.art = art
        self.color = random.choice(FISH_COLORS)
        self.speed = random.uniform(0.3, 1.1)
        self.y = random.randint(1, max(1, self.height - 4))
        self.wobble = random.uniform(0, 6.28)
        if initial:
            self.x = random.uniform(0, self.width - len(art))
        elif self.direction > 0:
            self.x = -float(len(art))
        else:
            self.x = float(self.width)

    def update(self, tick):
        self.x += self.speed * self.direction
        self.wobble += 0.15
        if self.direction > 0 and self.x > self.width:
            self.respawn()
        elif self.direction < 0 and self.x + len(self.art) < 0:
            self.respawn()

    def draw(self, grid):
        import math

        row = self.y + int(round(math.sin(self.wobble)))
        row = max(1, min(self.height - 3, row))
        col = int(self.x)
        for i, ch in enumerate(self.art):
            x = col + i
            if 0 <= x < self.width:
                grid[row][x] = (ch, self.color)


class Bubble:
    def __init__(self, width, height):
        self.width = width
        self.height = height
        self.reset()

    def reset(self):
        self.x = random.randint(0, self.width - 1)
        self.y = float(self.height - 3)
        self.speed = random.uniform(0.2, 0.6)
        self.char = random.choice(".oO°")

    def update(self):
        self.y -= self.speed
        if self.y < 1:
            self.reset()

    def draw(self, grid):
        row = int(self.y)
        if 1 <= row < self.height - 2 and 0 <= self.x < self.width:
            grid[row][self.x] = (self.char, BUBBLE_COLOR)


class Seaweed:
    def __init__(self, x, height):
        self.x = x
        self.height = height
        self.stalk = random.randint(3, max(3, height // 3))
        self.phase = random.uniform(0, 6.28)

    def draw(self, grid, tick):
        import math

        base = self.height - 3
        for i in range(self.stalk):
            sway = int(round(math.sin(tick * 0.1 + self.phase + i * 0.5)))
            x = self.x + sway
            y = base - i
            if 0 <= x < len(grid[0]) and 1 <= y < self.height - 2:
                grid[y][x] = ("(" if sway < 0 else ")", WEED_COLOR)


def render(grid, width, height):
    lines = []
    top = color(WATER_COLOR) + "~" * width + RESET
    lines.append(top)
    for row in grid[1 : height - 2]:
        parts = []
        last_color = None
        for ch, col in row:
            if col != last_color:
                parts.append(color(col))
                last_color = col
            parts.append(ch)
        parts.append(RESET)
        lines.append("".join(parts))
    sand = color(SAND_COLOR)
    lines.append(sand + "".join(random.Random(7).choice(".,_") for _ in range(width)) + RESET)
    lines.append(sand + "#" * width + RESET)
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description="ASCII aquarium")
    parser.add_argument("--frames", type=int, default=0, help="stop after N frames (0 = forever)")
    parser.add_argument("--fps", type=float, default=12.0, help="frames per second")
    parser.add_argument("--fish", type=int, default=0, help="number of fish (0 = auto)")
    args = parser.parse_args()

    size = shutil.get_terminal_size(fallback=(80, 24))
    width, height = size.columns, size.lines - 1
    width = max(20, width)
    height = max(10, height)

    n_fish = args.fish or max(3, (width * height) // 300)
    fishes = [Fish(width, height) for _ in range(n_fish)]
    bubbles = [Bubble(width, height) for _ in range(max(2, width // 15))]
    weeds = [Seaweed(x, height) for x in random.sample(range(2, width - 2), max(2, width // 12))]

    out = sys.stdout

    def cleanup(*_):
        out.write(SHOW_CURSOR + RESET + "\n")
        out.flush()
        sys.exit(0)

    signal.signal(signal.SIGINT, cleanup)
    out.write(HIDE_CURSOR + CLEAR)

    tick = 0
    delay = 1.0 / args.fps
    try:
        while args.frames == 0 or tick < args.frames:
            grid = [[(" ", WATER_COLOR) for _ in range(width)] for _ in range(height)]
            for weed in weeds:
                weed.draw(grid, tick)
            for bubble in bubbles:
                bubble.update()
                bubble.draw(grid)
            for fish in fishes:
                fish.update(tick)
                fish.draw(grid)
            out.write(HOME + render(grid, width, height))
            out.flush()
            tick += 1
            time.sleep(delay)
    finally:
        out.write(SHOW_CURSOR + RESET + "\n")
        out.flush()


if __name__ == "__main__":
    main()
