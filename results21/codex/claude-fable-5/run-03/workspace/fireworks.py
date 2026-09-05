#!/usr/bin/env python3
"""Terminal fireworks: a zero-dependency ANSI particle show.

Usage:
    python3 fireworks.py            # run until Ctrl-C
    python3 fireworks.py --seconds 10
    python3 fireworks.py --snapshot # print a single still frame (no cursor tricks)
"""

import argparse
import math
import os
import random
import sys
import time

GRAVITY = 12.0
SPARK_CHARS = ".+*o"
TRAIL_CHAR = "|"
PALETTES = [
    [196, 202, 208, 214, 220],   # ember
    [46, 82, 118, 154, 190],     # lime
    [21, 27, 33, 39, 45],        # blue
    [201, 200, 199, 198, 197],   # pink
    [51, 50, 49, 48, 47],        # teal
    [226, 227, 228, 229, 230],   # gold
]


class Particle:
    __slots__ = ("x", "y", "vx", "vy", "age", "life", "palette")

    def __init__(self, x, y, vx, vy, life, palette):
        self.x, self.y = x, y
        self.vx, self.vy = vx, vy
        self.age = 0.0
        self.life = life
        self.palette = palette

    def step(self, dt):
        self.age += dt
        self.vy += GRAVITY * dt
        self.vx *= 0.985
        self.x += self.vx * dt
        self.y += self.vy * dt

    @property
    def dead(self):
        return self.age >= self.life


class Rocket:
    __slots__ = ("x", "y", "vy", "fuse", "palette")

    def __init__(self, width, height):
        self.x = random.uniform(width * 0.15, width * 0.85)
        self.y = float(height - 1)
        self.vy = -random.uniform(height * 0.9, height * 1.4)
        self.fuse = random.uniform(0.5, 0.9)
        self.palette = random.choice(PALETTES)

    def step(self, dt):
        self.fuse -= dt
        self.vy += GRAVITY * dt * 0.4
        self.y += self.vy * dt

    def explode(self):
        count = random.randint(40, 80)
        speed = random.uniform(9, 16)
        parts = []
        for _ in range(count):
            angle = random.uniform(0, 6.28318)
            magnitude = speed * random.uniform(0.3, 1.0)
            parts.append(
                Particle(
                    self.x,
                    self.y,
                    math.cos(angle) * magnitude * 2.0,  # terminal cells are tall
                    math.sin(angle) * magnitude,
                    random.uniform(0.8, 1.6),
                    self.palette,
                )
            )
        return parts


def render(width, height, rockets, particles):
    grid = [[None] * width for _ in range(height)]
    for rocket in rockets:
        col, row = int(rocket.x), int(rocket.y)
        if 0 <= row < height and 0 <= col < width:
            grid[row][col] = (rocket.palette[0], TRAIL_CHAR)
    for particle in particles:
        col, row = int(particle.x), int(particle.y)
        if 0 <= row < height and 0 <= col < width:
            fade = particle.age / particle.life
            color = particle.palette[min(int(fade * len(particle.palette)), len(particle.palette) - 1)]
            char = SPARK_CHARS[min(int((1 - fade) * len(SPARK_CHARS)), len(SPARK_CHARS) - 1)]
            grid[row][col] = (color, char)
    lines = []
    for row in grid:
        chunks = []
        for cell in row:
            if cell is None:
                chunks.append(" ")
            else:
                color, char = cell
                chunks.append(f"\x1b[38;5;{color}m{char}\x1b[0m")
        lines.append("".join(chunks))
    return "\n".join(lines)


def simulate(width, height, seconds, draw):
    rockets, particles = [], []
    dt = 1 / 30
    elapsed = 0.0
    while seconds is None or elapsed < seconds:
        if random.random() < 0.06 or not (rockets or particles):
            rockets.append(Rocket(width, height))
        for rocket in rockets[:]:
            rocket.step(dt)
            if rocket.fuse <= 0 or rocket.vy > -2:
                rockets.remove(rocket)
                particles.extend(rocket.explode())
        for particle in particles[:]:
            particle.step(dt)
            if particle.dead or particle.y >= height:
                particles.remove(particle)
        draw(render(width, height, rockets, particles))
        elapsed += dt


def main():
    parser = argparse.ArgumentParser(description="ANSI terminal fireworks")
    parser.add_argument("--seconds", type=float, default=None, help="run time (default: forever)")
    parser.add_argument("--snapshot", action="store_true", help="print one still frame and exit")
    args = parser.parse_args()

    try:
        size = os.get_terminal_size()
        width, height = size.columns, size.lines - 1
    except OSError:
        width, height = 80, 24

    if args.snapshot:
        frames = []
        simulate(width, height, 1.2, frames.append)
        print(frames[-1])
        return

    sys.stdout.write("\x1b[2J\x1b[?25l")
    try:
        def draw(frame):
            sys.stdout.write("\x1b[H" + frame)
            sys.stdout.flush()
            time.sleep(1 / 30)

        simulate(width, height, args.seconds, draw)
    except KeyboardInterrupt:
        pass
    finally:
        sys.stdout.write("\x1b[0m\x1b[?25h\n")
        sys.stdout.flush()


if __name__ == "__main__":
    main()
