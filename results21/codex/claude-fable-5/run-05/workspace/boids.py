#!/usr/bin/env python3
"""Boids: an ASCII flocking simulation for your terminal.

Run:  python3 boids.py
Keys: q quit | space pause | +/- add/remove boids | p toggle predator
"""

import curses
import math
import random
import time

NUM_BOIDS = 40
VIEW_RADIUS = 8.0
SEP_RADIUS = 2.5
MAX_SPEED = 14.0
MIN_SPEED = 4.0
SEP_WEIGHT = 1.6
ALI_WEIGHT = 0.9
COH_WEIGHT = 0.7
FEAR_RADIUS = 10.0
FEAR_WEIGHT = 3.0
EDGE_MARGIN = 4.0
EDGE_WEIGHT = 6.0
DT = 1 / 30

GLYPHS = {  # heading (radians) -> arrow
    0: ">", 1: "\\", 2: "v", 3: "/", 4: "<", 5: "\\", 6: "^", 7: "/",
}


class Boid:
    def __init__(self, w, h):
        self.x = random.uniform(0, w)
        self.y = random.uniform(0, h)
        angle = random.uniform(0, 2 * math.pi)
        speed = random.uniform(MIN_SPEED, MAX_SPEED)
        self.vx = math.cos(angle) * speed
        self.vy = math.sin(angle) * speed

    def glyph(self):
        angle = math.atan2(self.vy, self.vx)
        octant = int(round(angle / (math.pi / 4))) % 8
        return GLYPHS[octant]


class Predator:
    def __init__(self, w, h):
        self.x, self.y = w / 2, h / 2
        self.vx, self.vy = 6.0, 3.0

    def update(self, w, h, boids):
        if boids:
            target = min(boids, key=lambda b: (b.x - self.x) ** 2 + (b.y - self.y) ** 2)
            dx, dy = target.x - self.x, target.y - self.y
            dist = math.hypot(dx, dy) or 1.0
            self.vx += (dx / dist) * 8.0 * DT
            self.vy += (dy / dist) * 8.0 * DT
        speed = math.hypot(self.vx, self.vy) or 1.0
        cap = MAX_SPEED * 0.75
        if speed > cap:
            self.vx, self.vy = self.vx / speed * cap, self.vy / speed * cap
        self.x = (self.x + self.vx * DT) % w
        self.y = (self.y + self.vy * DT) % h


def step(boids, predator, w, h):
    for b in boids:
        sep_x = sep_y = ali_x = ali_y = coh_x = coh_y = 0.0
        neighbors = 0
        for o in boids:
            if o is b:
                continue
            dx, dy = o.x - b.x, o.y - b.y
            d2 = dx * dx + dy * dy
            if d2 > VIEW_RADIUS * VIEW_RADIUS:
                continue
            neighbors += 1
            ali_x += o.vx
            ali_y += o.vy
            coh_x += o.x
            coh_y += o.y
            if d2 < SEP_RADIUS * SEP_RADIUS and d2 > 1e-9:
                inv = 1.0 / d2
                sep_x -= dx * inv
                sep_y -= dy * inv
        ax = ay = 0.0
        if neighbors:
            ax += SEP_WEIGHT * sep_x
            ay += SEP_WEIGHT * sep_y
            ax += ALI_WEIGHT * (ali_x / neighbors - b.vx) * 0.3
            ay += ALI_WEIGHT * (ali_y / neighbors - b.vy) * 0.3
            ax += COH_WEIGHT * (coh_x / neighbors - b.x) * 0.15
            ay += COH_WEIGHT * (coh_y / neighbors - b.y) * 0.15
        if predator is not None:
            dx, dy = b.x - predator.x, b.y - predator.y
            d = math.hypot(dx, dy)
            if 1e-9 < d < FEAR_RADIUS:
                ax += FEAR_WEIGHT * dx / d
                ay += FEAR_WEIGHT * dy / d
        if b.x < EDGE_MARGIN:
            ax += EDGE_WEIGHT
        elif b.x > w - EDGE_MARGIN:
            ax -= EDGE_WEIGHT
        if b.y < EDGE_MARGIN:
            ay += EDGE_WEIGHT
        elif b.y > h - EDGE_MARGIN:
            ay -= EDGE_WEIGHT
        b.vx += ax * DT * 10
        b.vy += ay * DT * 10
        speed = math.hypot(b.vx, b.vy) or 1.0
        if speed > MAX_SPEED:
            b.vx, b.vy = b.vx / speed * MAX_SPEED, b.vy / speed * MAX_SPEED
        elif speed < MIN_SPEED:
            b.vx, b.vy = b.vx / speed * MIN_SPEED, b.vy / speed * MIN_SPEED
        b.x = min(max(b.x + b.vx * DT, 0.0), w - 1e-6)
        b.y = min(max(b.y + b.vy * DT, 0.0), h - 1e-6)


def main(stdscr):
    try:
        curses.curs_set(0)
    except curses.error:
        pass
    stdscr.nodelay(True)
    has_color = curses.has_colors()
    if has_color:
        curses.start_color()
        curses.use_default_colors()
        curses.init_pair(1, curses.COLOR_CYAN, -1)
        curses.init_pair(2, curses.COLOR_RED, -1)
        curses.init_pair(3, curses.COLOR_YELLOW, -1)

    h, w = stdscr.getmaxyx()
    # simulate in a space twice as wide as tall-cells to compensate glyph aspect
    boids = [Boid(w - 1, h - 2) for _ in range(NUM_BOIDS)]
    predator = Predator(w - 1, h - 2)
    paused = False

    while True:
        key = stdscr.getch()
        if key in (ord("q"), 27):
            break
        elif key == ord(" "):
            paused = not paused
        elif key in (ord("+"), ord("=")):
            boids.append(Boid(w - 1, h - 2))
        elif key == ord("-") and boids:
            boids.pop()
        elif key == ord("p"):
            predator = None if predator else Predator(w - 1, h - 2)
        elif key == curses.KEY_RESIZE:
            h, w = stdscr.getmaxyx()

        if not paused:
            step(boids, predator, w - 1, h - 2)
            if predator is not None:
                predator.update(w - 1, h - 2, boids)

        stdscr.erase()
        for b in boids:
            attr = curses.color_pair(1) if has_color else 0
            try:
                stdscr.addch(int(b.y), int(b.x), b.glyph(), attr)
            except curses.error:
                pass
        if predator is not None:
            attr = curses.color_pair(2) | curses.A_BOLD if has_color else curses.A_BOLD
            try:
                stdscr.addch(int(predator.y), int(predator.x), "@", attr)
            except curses.error:
                pass
        status = f" boids:{len(boids)}  predator:{'on' if predator else 'off'}  [q]uit [space]pause [+/-] [p] "
        attr = curses.color_pair(3) if has_color else curses.A_REVERSE
        try:
            stdscr.addnstr(h - 1, 0, status.ljust(w - 1), w - 1, attr)
        except curses.error:
            pass
        stdscr.refresh()
        time.sleep(DT)


if __name__ == "__main__":
    curses.wrapper(main)
