#!/usr/bin/env python3
"""Terminal ASCII fireworks animation.

Launches colorful firework particles that rise, explode, and fade,
rendered entirely in the terminal using the standard `curses` module.
No third-party dependencies required.

Usage:
    python3 fireworks.py [--fps FPS] [--density DENSITY]

Press 'q' or Ctrl-C to quit.
"""

import argparse
import curses
import math
import random
import time

PARTICLE_CHARS = ".oO*+^`'"
TRAIL_CHAR = "|"


class Particle:
    """A single spark within an exploded firework."""

    def __init__(self, x, y, color):
        angle = random.uniform(0, 2 * math.pi)
        speed = random.uniform(0.4, 1.6)
        self.x = x
        self.y = y
        self.vx = math.cos(angle) * speed
        self.vy = math.sin(angle) * speed * 0.6
        self.color = color
        self.life = random.uniform(1.0, 2.2)
        self.age = 0.0
        self.char = random.choice(PARTICLE_CHARS)

    def step(self, dt, gravity):
        self.age += dt
        self.vy += gravity * dt
        self.x += self.vx * dt * 12
        self.y += self.vy * dt * 12
        return self.age < self.life

    def alive_ratio(self):
        return max(0.0, 1.0 - self.age / self.life)


class Rocket:
    """A rising firework before it explodes."""

    def __init__(self, x, y_start, y_target, color):
        self.x = x
        self.y = y_start
        self.y_target = y_target
        self.color = color
        self.vy = -random.uniform(1.6, 2.2)
        self.exploded = False
        self.trail = []

    def step(self, dt):
        self.trail.append((self.x, self.y))
        if len(self.trail) > 6:
            self.trail.pop(0)
        self.y += self.vy * dt * 12
        if self.y <= self.y_target:
            self.exploded = True
        return not self.exploded


def make_explosion(x, y, color, count):
    return [Particle(x, y, color) for _ in range(count)]


def run(stdscr, fps, density):
    try:
        curses.curs_set(0)
    except curses.error:
        pass
    stdscr.nodelay(True)
    curses.start_color()
    curses.use_default_colors()

    color_pairs = [
        curses.COLOR_RED,
        curses.COLOR_YELLOW,
        curses.COLOR_GREEN,
        curses.COLOR_CYAN,
        curses.COLOR_MAGENTA,
        curses.COLOR_WHITE,
        curses.COLOR_BLUE,
    ]
    for i, c in enumerate(color_pairs, start=1):
        curses.init_pair(i, c, -1)

    height, width = stdscr.getmaxyx()
    rockets = []
    particles = []
    dt = 1.0 / fps
    last_launch = 0.0
    launch_interval = max(0.15, 1.2 / density)

    while True:
        try:
            key = stdscr.getch()
        except curses.error:
            key = -1
        if key in (ord("q"), ord("Q")):
            break

        new_h, new_w = stdscr.getmaxyx()
        if (new_h, new_w) != (height, width):
            height, width = new_h, new_w

        last_launch += dt
        if last_launch >= launch_interval and width > 10 and height > 6:
            last_launch = 0.0
            x = random.uniform(width * 0.1, width * 0.9)
            y_target = random.uniform(height * 0.15, height * 0.55)
            color = random.randint(1, len(color_pairs))
            rockets.append(Rocket(x, height - 1, y_target, color))

        stdscr.erase()

        still_rising = []
        for r in rockets:
            alive = r.step(dt)
            for tx, ty in r.trail:
                ix, iy = int(tx), int(ty)
                if 0 <= iy < height and 0 <= ix < width:
                    try:
                        stdscr.addstr(iy, ix, TRAIL_CHAR, curses.color_pair(r.color))
                    except curses.error:
                        pass
            if alive:
                still_rising.append(r)
            else:
                particles.extend(make_explosion(r.x, r.y, r.color, random.randint(20, 40)))
        rockets = still_rising

        still_alive = []
        for p in particles:
            alive = p.step(dt, gravity=0.5)
            ix, iy = int(p.x), int(p.y)
            if 0 <= iy < height and 0 <= ix < width:
                ratio = p.alive_ratio()
                attr = curses.color_pair(p.color)
                if ratio < 0.35:
                    attr |= curses.A_DIM
                try:
                    stdscr.addstr(iy, ix, p.char, attr)
                except curses.error:
                    pass
            if alive:
                still_alive.append(p)
        particles = still_alive

        try:
            stdscr.addstr(0, 0, " Fireworks -- press q to quit ", curses.A_DIM)
        except curses.error:
            pass

        stdscr.refresh()
        time.sleep(dt)


def main():
    parser = argparse.ArgumentParser(description="Terminal ASCII fireworks animation.")
    parser.add_argument("--fps", type=float, default=30.0, help="Frames per second (default: 30)")
    parser.add_argument(
        "--density",
        type=float,
        default=1.0,
        help="Relative launch frequency, higher is busier (default: 1.0)",
    )
    args = parser.parse_args()

    try:
        curses.wrapper(run, args.fps, args.density)
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()
