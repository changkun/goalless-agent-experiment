#!/usr/bin/env python3
"""
🐠 Claude's ASCII Aquarium 🐟
Sit back and watch the fish swim.
"""

import os
import sys
import time
import random
import shutil
import signal

# Graceful exit
signal.signal(signal.SIGINT, lambda *_: (print("\033[?25h\033[0m"), sys.exit(0)))

COLS, ROWS = shutil.get_terminal_size((80, 24))
ROWS -= 1  # Leave room for status line

# Colors (ANSI)
CYAN    = "\033[36m"
BLUE    = "\033[34m"
GREEN   = "\033[32m"
YELLOW  = "\033[33m"
RED     = "\033[31m"
MAGENTA = "\033[35m"
WHITE   = "\033[97m"
DIM     = "\033[2m"
RESET   = "\033[0m"
HIDE    = "\033[?25l"
SHOW    = "\033[?25h"
BOLD    = "\033[1m"

FISH_COLORS = [CYAN, BLUE, GREEN, YELLOW, RED, MAGENTA, WHITE]

FISH_RIGHT = [
    "><>",
    ">»>",
    "◉≻≻",
    "►▷►",
    ">⟫>",
    "⋗⋗⋗",
    ">❯>",
]

FISH_LEFT = [
    "<><",
    "<«<",
    "≺≺◉",
    "◁◀◁",
    "<⟪<",
    "⋖⋖⋖",
    "<❮<",
]

# Seaweed patterns
SEAWEED_CHARS = ["║", "╟", "╢", "┃", "╽", "╿", "│"]

# Bubble characters
BUBBLE_CHARS = ["°", "o", "O", "∘", "·", "•"]


class Fish:
    def __init__(self):
        self.x = random.randint(0, COLS - 6)
        self.y = random.randint(1, ROWS - 2)
        self.speed = random.uniform(0.3, 1.0)
        self.direction = random.choice([-1, 1])
        self.color = random.choice(FISH_COLORS)
        body_idx = random.randint(0, len(FISH_RIGHT) - 1)
        self.body_r = FISH_RIGHT[body_idx]
        self.body_l = FISH_LEFT[body_idx]
        self.offset = 0.0
        self.wobble = random.uniform(0, 6.28)
        self.wobble_amt = random.uniform(0.1, 0.4)

    def update(self, tick):
        self.offset += self.speed
        self.wobble += 0.15

        if self.offset > 1:
            self.offset = 0
            self.x += self.direction

        # Wrap around
        if self.x > COLS:
            self.x = -4
        if self.x < -4:
            self.x = COLS

        # Occasional direction change
        if random.random() < 0.005:
            self.direction *= -1

    @property
    def display_y(self):
        return int(self.y + math.sin(self.wobble) * self.wobble_amt)

    def draw(self, tick):
        y = max(0, min(ROWS - 1, self.display_y))
        body = self.body_r if self.direction > 0 else self.body_l
        return (int(self.x), y, body, self.color)


class Bubble:
    def __init__(self, x=None):
        self.x = x if x else random.randint(1, COLS - 1)
        self.y = ROWS - 1
        self.speed = random.uniform(0.2, 0.6)
        self.offset = 0.0
        self.char = random.choice(BUBBLE_CHARS)
        self.wobble = random.uniform(0, 6.28)

    def update(self, tick):
        self.offset += self.speed
        self.wobble += 0.1

    @property
    def display_y(self):
        return int(self.y - self.offset)

    @property
    def display_x(self):
        return int(self.x + math.sin(self.wobble) * 0.8)

    def alive(self):
        return self.display_y >= 0


class Seaweed:
    def __init__(self, x):
        self.x = x
        self.height = random.randint(3, 8)
        self.phase = random.uniform(0, 6.28)
        self.shade = random.choice([GREEN, DIM + GREEN])

    def draw(self, tick):
        segments = []
        self.phase += 0.05
        for i in range(self.height):
            y = ROWS - 1 - i
            if 0 <= y < ROWS:
                sway = int(math.sin(self.phase + i * 0.5) * 0.7)
                char = random.choice(SEAWEED_CHARS) if i > 0 else "╨"
                segments.append((self.x + sway, y, char, self.shade))
        return segments


import math


def make_sand():
    """Generate a sandy bottom row."""
    sand_chars = ["▀", "▄", "░", "▒", "~", "_"]
    return "".join(random.choices(sand_chars, k=COLS))


def main():
    # Initialize
    fishies = [Fish() for _ in range(random.randint(8, 14))]
    bubbles = []
    seaweeds = [Seaweed(x) for x in sorted(random.sample(range(2, COLS - 2), min(8, COLS // 10)))]

    sand = make_sand()
    tick = 0
    frame_time = 1.0 / 15  # ~15 FPS

    # Hide cursor, clear screen
    sys.stdout.write(HIDE + "\033[2J")
    sys.stdout.flush()

    try:
        while True:
            tick += 1
            start = time.time()

            # Spawn bubbles occasionally
            if random.random() < 0.15:
                # Bubbles from seaweed or random
                if seaweeds and random.random() < 0.5:
                    bubbles.append(Bubble(random.choice(seaweeds).x))
                else:
                    bubbles.append(Bubble())

            # Update
            for f in fishies:
                f.update(tick)
            for b in bubbles:
                b.update(tick)
            bubbles = [b for b in bubbles if b.alive()]

            # Build frame buffer
            buf = {}

            # Draw water effect (subtle)
            water_color = DIM + BLUE if tick % 60 < 45 else DIM + CYAN

            # Draw seaweed
            for sw in seaweeds:
                for sx, sy, sc, scol in sw.draw(tick):
                    key = (sx, sy)
                    if 0 <= sx < COLS and 0 <= sy < ROWS:
                        buf[key] = (sc, scol)

            # Draw bubbles
            for b in bubbles:
                bx, by = b.display_x, b.display_y
                if 0 <= bx < COLS and 0 <= by < ROWS:
                    buf[(bx, by)] = (b.char, DIM + CYAN)

            # Draw fish
            for f in fishies:
                fx, fy, fbody, fcolor = f.draw(tick)
                for i, ch in enumerate(fbody):
                    px = fx + i
                    if 0 <= px < COLS and 0 <= fy < ROWS:
                        buf[(px, fy)] = (ch, fcolor)

            # Render to screen
            lines = []
            for y in range(ROWS):
                row_str = ""
                col = 0
                while col < COLS:
                    if (col, y) in buf:
                        ch, color = buf[(col, y)]
                        row_str += f"{color}{ch}{RESET}"
                        col += 1
                    else:
                        # Water background
                        row_str += " "
                        col += 1
                lines.append(row_str)

            # Sand bottom
            sand_line = f"{YELLOW}{DIM}{sand}{RESET}"

            # Status bar
            elapsed = time.time() - start
            fish_count = len(fishies)
            bubble_count = len(bubbles)
            status = f"{BOLD}🐠 Claude's ASCII Aquarium{RESET}  │  {CYAN}{fish_count}{RESET} fish  │  {DIM}{bubble_count} bubbles{RESET}  │  {DIM}Ctrl+C to exit{RESET}"

            # Move cursor home and draw
            sys.stdout.write("\033[H")
            sys.stdout.write("\n".join(lines) + "\n" + sand_line + "\n" + status + "\033[0m")
            sys.stdout.flush()

            # Frame rate limiting
            sleep_time = frame_time - (time.time() - start)
            if sleep_time > 0:
                time.sleep(sleep_time)

    except KeyboardInterrupt:
        pass
    finally:
        sys.stdout.write(SHOW + RESET + "\033[2J\033[H")
        print(f"\n{BOLD}Thanks for watching! 🐟{RESET}\n")


if __name__ == "__main__":
    main()
