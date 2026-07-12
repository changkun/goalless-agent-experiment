#!/usr/bin/env python3
"""
Terminal Conway's Game of Life — colorful, interactive, and alive.

Controls:
  r        — randomize the grid
  g        — drop a Gosper glider gun at cursor
  p        — drop a pulsar at cursor
  space    — pause / resume
  c        — clear the grid
  q / ESC  — quit
  arrows   — move cursor
  enter    — toggle cell at cursor
  + / -    — speed up / slow down

Cells age with color: newborn → youth → adult → elder → death.
Needs a real terminal (not piped/non-TTY).
"""

import os
import sys
import time
import signal
import random
import select
import threading
import termios
import tty
from dataclasses import dataclass


# ── Terminal setup ──────────────────────────────────────────────────────────

def setup_terminal():
    """Switch to raw mode, hide cursor. Returns old settings."""
    fd = sys.stdin.fileno()
    old = termios.tcgetattr(fd)
    tty.setraw(fd)
    sys.stdout.write("\033[?25l")  # hide cursor
    sys.stdout.flush()
    return old


def restore_terminal(old):
    """Restore terminal and show cursor."""
    sys.stdout.write("\033[?25h\033[0m")  # show cursor, reset colors
    sys.stdout.flush()
    termios.tcsetattr(sys.stdin.fileno(), termios.TCSADRAIN, old)


def term_size():
    s = os.get_terminal_size()
    return s.lines, s.columns


# ── ANSI helpers ────────────────────────────────────────────────────────────

CURSOR_HOME  = "\033[H"
CLEAR_SCREEN = "\033[2J"
RESET        = "\033[0m"


def cell_color(age: int) -> str:
    """Age → 256-color ANSI foreground (cyan → green → yellow → red → violet)."""
    if age <= 0:
        return ""
    palette = [51, 45, 39, 33, 220, 214, 208, 202, 196, 200, 205, 170, 135, 99, 63]
    idx = min(age - 1, len(palette) - 1)
    return f"\033[38;5;{palette[idx]}m"


# ── Patterns ────────────────────────────────────────────────────────────────

GOSPER_GUN = [
    (0, 24),
    (1, 22), (1, 24),
    (2, 12), (2, 13), (2, 20), (2, 21), (2, 34), (2, 35),
    (3, 11), (3, 15), (3, 20), (3, 21), (3, 34), (3, 35),
    (4, 0),  (4, 1),  (4, 10), (4, 16), (4, 20), (4, 21),
    (5, 0),  (5, 1),  (5, 10), (5, 14), (5, 16), (5, 17), (5, 22), (5, 24),
    (6, 10), (6, 16), (6, 24),
    (7, 11), (7, 15),
    (8, 12), (8, 13),
]


def _pulsar_quadrant():
    """Top-left quadrant offsets for a 15×15 pulsar."""
    return [
        (2, 4), (2, 5), (2, 6), (4, 2), (5, 2), (6, 2),
        (4, 7), (5, 7), (6, 7), (7, 4), (7, 5), (7, 6),
    ]


def pulsar():
    """Full 15×15 pulsar (period-3 oscillator) via mirroring."""
    coords = []
    for r, c in _pulsar_quadrant():
        for (rr, cc) in [(r, c), (r, 14 - c), (14 - r, c), (14 - r, 14 - c)]:
            coords.append((rr, cc))
    return coords


# ── World ───────────────────────────────────────────────────────────────────

class World:
    def __init__(self, rows, cols):
        self.rows = rows
        self.cols = cols
        self.grid = [[0] * cols for _ in range(rows)]
        self._next = [[0] * cols for _ in range(rows)]
        self.generation = 0
        self.population = 0

    def clear(self):
        for r in range(self.rows):
            row = self.grid[r]
            for c in range(self.cols):
                row[c] = 0
        self.generation = 0
        self.population = 0

    def randomize(self, density=0.3):
        self.clear()
        for r in range(self.rows):
            row = self.grid[r]
            for c in range(self.cols):
                if random.random() < density:
                    row[c] = 1
                    self.population += 1

    def place_pattern(self, pattern, top, left):
        for dr, dc in pattern:
            r = (top + dr) % self.rows
            c = (left + dc) % self.cols
            if self.grid[r][c] == 0:
                self.population += 1
            self.grid[r][c] = 1

    def toggle(self, r, c):
        if self.grid[r][c] > 0:
            self.grid[r][c] = 0
            self.population -= 1
        else:
            self.grid[r][c] = 1
            self.population += 1

    def tick(self):
        self.generation += 1
        pop = 0
        R, C = self.rows, self.cols
        grid, nxt = self.grid, self._next

        for r in range(R):
            g_row = grid[r]
            n_row = nxt[r]
            up   = grid[(r - 1) % R]
            down = grid[(r + 1) % R]

            for c in range(C):
                # Inline neighbor count — faster than a loop
                n = (
                    up[(c - 1) % C]   + up[c]   + up[(c + 1) % C] +
                    g_row[(c - 1) % C] +           g_row[(c + 1) % C] +
                    down[(c - 1) % C] + down[c] + down[(c + 1) % C]
                )
                age = g_row[c]
                if age > 0:
                    if n == 2 or n == 3:
                        n_row[c] = age + 1
                        pop += 1
                    else:
                        n_row[c] = 0
                else:
                    if n == 3:
                        n_row[c] = 1
                        pop += 1
                    else:
                        n_row[c] = 0

        self.grid, self._next = nxt, grid
        self.population = pop


# ── Render ──────────────────────────────────────────────────────────────────

def render(world, cur_r, cur_c, paused, speed):
    rows, cols = world.rows, world.cols
    buf = [CURSOR_HOME, "\033[48;5;232m"]  # dark bg

    for r in range(rows):
        for c in range(cols):
            age = world.grid[r][c]
            is_cursor = (r == cur_r and c == cur_c)
            bg = "\033[48;5;237m" if is_cursor else ""

            if age > 0:
                color = cell_color(age)
                glyph = "●" if age >= 3 else "○" if age == 1 else "◎"
                buf.append(f"{bg}{color}{glyph}")
            else:
                buf.append(f"{bg}\033[38;5;235m·")
        if r < rows - 1:
            buf.append("\n")

    buf.append(RESET)
    status = "PAUSED" if paused else "RUNNING"
    buf.append(
        f"\n\033[48;5;236m\033[38;5;250m"
        f" Gen:{world.generation:>7,}  Pop:{world.population:>6,}  {status:7s}  "
        f"{speed:3.0f} tps  "
        f"[r]and [g]un [p]ulsar [c]lear [space] ⏯  [+/-] ⇅  arrows/enter [q]uit"
        f"\033[K{RESET}"
    )
    sys.stdout.write("".join(buf))
    sys.stdout.flush()


# ── Input reader thread ─────────────────────────────────────────────────────

def input_reader(stop_event, queue):
    """Background thread: push raw key sequences into queue."""
    fd = sys.stdin.fileno()
    while not stop_event.is_set():
        if select.select([fd], [], [], 0.05)[0]:
            ch = os.read(fd, 1)
            if not ch:
                continue
            ch = ch.decode("utf-8", errors="replace")
            if ch == "\033":
                # Try to read the rest of the escape sequence
                try:
                    ch += os.read(fd, 2).decode("utf-8", errors="replace")
                except Exception:
                    pass
            queue.append(ch)


# ── Main ────────────────────────────────────────────────────────────────────

def main():
    if not sys.stdin.isatty():
        print("This game needs a real terminal. Run it interactively!")
        sys.exit(1)

    old_term = setup_terminal()
    stop = threading.Event()
    key_queue = []
    reader = threading.Thread(
        target=input_reader, args=(stop, key_queue), daemon=True
    )

    try:
        rows, cols = term_size()
        world_rows = max(10, rows - 2)
        world_cols = max(20, cols)
        world = World(world_rows, world_cols)

        cur_r, cur_c = world_rows // 2, world_cols // 2
        paused = True
        speed = 10.0      # generations per second
        tick_acc = 0.0
        last_t = time.monotonic()

        sys.stdout.write(CLEAR_SCREEN)
        sys.stdout.flush()

        # Seed with some action
        world.place_pattern(GOSPER_GUN, 3, 6)
        world.place_pattern(pulsar(), world_rows // 2 - 7, world_cols // 2 - 7)
        world.randomize(0.04)

        reader.start()

        while True:
            # Drain input
            while key_queue:
                k = key_queue.pop(0)
                if k == "q" or k == "\033":      # quit
                    return
                elif k == " ":
                    paused = not paused
                elif k == "r":
                    world.randomize(0.3)
                elif k == "g":
                    world.place_pattern(GOSPER_GUN, cur_r, cur_c)
                elif k == "p":
                    world.place_pattern(pulsar(), cur_r, cur_c)
                elif k == "c":
                    world.clear()
                elif k in ("\r", "\n"):
                    world.toggle(cur_r, cur_c)
                elif k in ("+", "="):
                    speed = min(60, speed + 5)
                elif k in ("-", "_"):
                    speed = max(1, speed - 5)
                elif k == "\033[A":               # ↑
                    cur_r = (cur_r - 1) % world_rows
                elif k == "\033[B":               # ↓
                    cur_r = (cur_r + 1) % world_rows
                elif k == "\033[C":               # →
                    cur_c = (cur_c + 1) % world_cols
                elif k == "\033[D":               # ←
                    cur_c = (cur_c - 1) % world_cols
                elif len(k) > 1:
                    pass  # unknown escape sequence

            # Advance
            now = time.monotonic()
            dt = now - last_t
            last_t = now

            if not paused:
                tick_acc += dt * speed
                nticks = int(tick_acc)
                for _ in range(nticks):
                    world.tick()
                tick_acc -= nticks

            render(world, cur_r, cur_c, paused, speed)
            time.sleep(0.025)  # ~40 fps

    except KeyboardInterrupt:
        pass
    finally:
        stop.set()
        reader.join(timeout=0.5)
        restore_terminal(old_term)
        sys.stdout.write(CLEAR_SCREEN)
        print("🌌 Thanks for playing Conway's Game of Life!")


if __name__ == "__main__":
    main()
