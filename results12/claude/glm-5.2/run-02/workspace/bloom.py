#!/usr/bin/env python3
"""
bloom — a terminal cellular automaton garden.

Each step, the grid evolves under a color-coupled rule:
  A cell's next color depends on its current color and the colors of
  its 8 neighbors. Life-like birth/survival is colored by which
  neighbors contributed, producing blooming, iridescent patterns
  instead of plain black/white Conway.

Controls (stdin, non-blocking):
  space  pause / resume
  r      reseed with a new random garden
  c      clear to black
  s      seed a centered glider gun-ish splash
  q      quit
"""
import os
import sys
import tty
import termios
import select
import time
import random
import signal

# ---- ANSI 24-bit color helpers -------------------------------------------
ESC = "\033"
def home():       return ESC + "[H"
def clear():      return ESC + "[2J" + ESC + "[H"
def hide_cursor(): return ESC + "[?25l"
def show_cursor(): return ESC + "[?25h"
def fg(r, g, b):  return f"{ESC}[38;2;{r};{g};{b}m"
def move(y, x):   return f"{ESC}[{y};{x}H"
RESET = ESC + "[0m"

# Cell states: 0 = empty, 1..N = colors
N_COLORS = 6
# Palette tuned for a dark terminal — jewel tones.
PALETTE = [
    (12, 14, 22),       # 0: background (deep navy)
    (255, 120, 90),     # 1: coral
    (90, 220, 180),     # 2: teal
    (240, 200, 80),     # 3: gold
    (180, 110, 240),    # 4: violet
    (110, 180, 255),    # 5: sky
    (255, 90, 160),     # 6: magenta
]

def glyph_for(color):
    # vary the character by color for texture
    return ".*+o=#@"[color % 7] if color else " "

# ---- Non-blocking stdin ---------------------------------------------------
_old_settings = None
def set_raw():
    global _old_settings
    fd = sys.stdin.fileno()
    _old_settings = termios.tcgetattr(fd)
    tty.setraw(fd)

def restore():
    if _old_settings:
        termios.tcsetattr(0, termios.TCSADRAIN, _old_settings)

def key_ready():
    return select.select([sys.stdin], [], [], 0) == ([sys.stdin], [], [])

def read_key():
    ch = sys.stdin.read(1)
    if ch == "\x1b":  # swallow arrow keys
        sys.stdin.read(2)
        return ""
    return ch

# ---- World ----------------------------------------------------------------
class World:
    def __init__(self, w, h):
        self.w, self.h = w, h
        self.grid = [[0]*w for _ in range(h)]
        self.generation = 0

    def seed_random(self, density=0.28):
        for y in range(self.h):
            for x in range(self.w):
                if random.random() < density:
                    self.grid[y][x] = random.randint(1, N_COLORS)
                else:
                    self.grid[y][x] = 0
        self.generation = 0

    def seed_splash(self):
        for y in range(self.h):
            for x in range(self.w):
                self.grid[y][x] = 0
        # a few gliders in different colors, aimed at the center
        cx, cy = self.w//2, self.h//2
        glider = [(0,1),(1,2),(2,0),(2,1),(2,2)]
        for (gy, gx) in glider:
            self.grid[(cy+gy) % self.h][(cx+gx) % self.w] = 3
        for (gy, gx) in glider:
            self.grid[(cy-6+gy) % self.h][(cx-10+gx) % self.w] = 1
        for (gy, gx) in glider:
            self.grid[(cy-6+gy) % self.h][(cx+10+gx) % self.w] = 5
        self.generation = 0

    def clear(self):
        for y in range(self.h):
            for x in range(self.w):
                self.grid[y][x] = 0
        self.generation = 0

    def step(self):
        w, h = self.w, self.h
        g = self.grid
        nxt = [[0]*w for _ in range(h)]
        for y in range(h):
            row_above = g[(y-1) % h]
            row = g[y]
            row_below = g[(y+1) % h]
            for x in range(w):
                # count alive neighbors and tally their colors
                counts = [0]*(N_COLORS+1)
                alive = 0
                xm = (x-1) % w
                xp = (x+1) % w
                for (ny, nx) in ((y-1, xm), (y-1, x), (y-1, xp),
                                 (y,   xm),           (y,   xp),
                                 (y+1, xm), (y+1, x), (y+1, xp)):
                    nr = g[ny % h][nx % w]
                    if nr:
                        alive += 1
                        counts[nr] += 1
                cell = row[x]
                if cell:  # alive: survive on 1..3 live neighbors (relaxed)
                    if 1 <= alive <= 3:
                        # drift color toward dominant neighbor color
                        dom = max(range(1, N_COLORS+1), key=lambda c: counts[c])
                        if counts[dom] >= 2:
                            nxt[y][x] = dom
                        else:
                            nxt[y][x] = cell
                    else:
                        nxt[y][x] = 0
                else:  # dead: born with exactly 3 neighbors (Conway-ish)
                    if alive == 3:
                        dom = max(range(1, N_COLORS+1), key=lambda c: counts[c])
                        nxt[y][x] = dom
                    else:
                        nxt[y][x] = 0
        self.grid = nxt
        self.generation += 1

# ---- Renderer -------------------------------------------------------------
def render(world, paused=False):
    # Build the whole frame as one string with per-cell color runs.
    out = [home()]
    for y in range(world.h):
        row = world.grid[y]
        prev = -1
        buf = []
        for x in range(world.w):
            c = row[x]
            if c != prev:
                r, g, b = PALETTE[c]
                buf.append(fg(r, g, b))
                prev = c
            buf.append(glyph_for(c))
        buf.append(ESC + "[K")  # clear to end of line
        out.append("".join(buf))
        out.append("\r\n")
    # status line
    out.append(fg(120, 140, 160))
    out.append(f"gen {world.generation:>6} "
               f"{'[PAUSED]' if paused else '         '}  "
               f"[space]pause  [r]reseed  [c]clear  [s]splash  [q]uit"
               + ESC + "[K")
    sys.stdout.write("".join(out))
    sys.stdout.flush()

def resize_handler(signum, frame):
    # just let the next loop iteration re-read size
    pass

def get_size():
    try:
        cols = int(os.environ.get("COLUMNS", 0)) or os.get_terminal_size(0).columns
        rows = int(os.environ.get("LINES", 0)) or os.get_terminal_size(0).lines
    except OSError:
        cols, rows = 80, 24
    return max(cols, 10), max(rows, 4)

# ---- Main -----------------------------------------------------------------
def main():
    cols, rows = get_size()
    w, h = cols, max(rows-2, 4)
    world = World(w, h)
    world.seed_random()
    paused = False

    signal.signal(signal.SIGWINCH, resize_handler)

    sys.stdout.write(clear() + hide_cursor())
    set_raw()
    try:
        last = time.monotonic()
        while True:
            cols, rows = get_size()
            if cols != w or (rows-2) != h:
                w, h = cols, max(rows-2, 4)
                world.w, world.h = w, h
                world.grid = [[0]*w for _ in range(h)]
                world.seed_random()

            while key_ready():
                k = read_key()
                if k == "q":
                    return
                elif k == " ":
                    paused = not paused
                elif k == "r":
                    world.seed_random()
                elif k == "c":
                    world.clear()
                elif k == "s":
                    world.seed_splash()

            if not paused:
                world.step()
            render(world, paused)

            # pace to ~20 fps
            elapsed = time.monotonic() - last
            last = time.monotonic()
            time.sleep(max(0.0, 0.05 - elapsed))
    finally:
        restore()
        sys.stdout.write(show_cursor() + move(h+2, 0) + "\n")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        restore()
        sys.stdout.write(show_cursor() + "\n")
