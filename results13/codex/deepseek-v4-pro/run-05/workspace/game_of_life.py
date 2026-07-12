#!/usr/bin/env python3
"""Conway's Game of Life — interactive terminal edition."""

import argparse
import os
import random
import signal
import sys
import termios
import time
import tty


# ── glyphs ──────────────────────────────────────────────────────────────────

ALIVE = "██"
DEAD = "  "
HEADER_COLOUR = "\033[1;36m"
CELL_COLOUR = "\033[1;32m"
RESET = "\033[0m"
CLEAR = "\033[2J\033[H"
CURSOR_HIDE = "\033[?25l"
CURSOR_SHOW = "\033[?25h"


# ── helpers ─────────────────────────────────────────────────────────────────

def parse_args():
    p = argparse.ArgumentParser(description="Conway's Game of Life in the terminal")
    p.add_argument("-r", "--rows", type=int, default=30, help="grid height")
    p.add_argument("-c", "--cols", type=int, default=40, help="grid width")
    p.add_argument("-d", "--density", type=float, default=0.3,
                   help="initial live-cell probability (0-1)")
    p.add_argument("-g", "--glider", action="store_true",
                   help="start with a single glider instead of random seed")
    p.add_argument("-f", "--fps", type=int, default=12,
                   help="target frames per second")
    return p.parse_args()


def term_size():
    """Best-effort terminal dimensions; fall back to 80x24."""
    try:
        rows, cols = os.get_terminal_size()
        return max(rows, 8), max(cols, 20)
    except (OSError, ValueError):
        return 24, 80


# ── keyboard input (non-blocking) ───────────────────────────────────────────

class RawInput:
    """Context manager that puts the terminal in raw mode, restoring on exit."""

    def __init__(self):
        self.fd = sys.stdin.fileno()
        self.original = None

    def __enter__(self):
        self.original = termios.tcgetattr(self.fd)
        tty.setraw(self.fd)
        flags = termios.tcgetattr(self.fd)
        flags[6][termios.VMIN] = 0
        flags[6][termios.VTIME] = 0
        termios.tcsetattr(self.fd, termios.TCSANOW, flags)
        return self

    def __exit__(self, *args):
        termios.tcsetattr(self.fd, termios.TCSAFLUSH, self.original)

    @staticmethod
    def getch():
        """Return a keypress as a string, or '' if nothing is available."""
        try:
            return sys.stdin.read(1)
        except (OSError, ValueError):
            return ''


# ── grid helpers ────────────────────────────────────────────────────────────

def new_grid(rows, cols):
    return [[False] * cols for _ in range(rows)]


def random_grid(rows, cols, density):
    return [[random.random() < density for _ in range(cols)] for _ in range(rows)]


def place_glider(grid, r, c):
    """Place a standard glider at (r, c) — top-left anchor."""
    pattern = [(0, 1), (1, 2), (2, 0), (2, 1), (2, 2)]
    rows, cols = len(grid), len(grid[0])
    for dr, dc in pattern:
        nr, nc = (r + dr) % rows, (c + dc) % cols
        grid[nr][nc] = True


def alive_neighbours(grid, r, c):
    rows, cols = len(grid), len(grid[0])
    count = 0
    for dr in (-1, 0, 1):
        for dc in (-1, 0, 1):
            if dr == 0 and dc == 0:
                continue
            nr = (r + dr) % rows
            nc = (c + dc) % cols
            if grid[nr][nc]:
                count += 1
    return count


def next_gen(grid):
    rows, cols = len(grid), len(grid[0])
    nxt = new_grid(rows, cols)
    for r in range(rows):
        for c in range(cols):
            n = alive_neighbours(grid, r, c)
            if grid[r][c]:
                nxt[r][c] = n in (2, 3)
            else:
                nxt[r][c] = n == 3
    return nxt


def population(grid):
    return sum(sum(row) for row in grid)


# ── rendering ───────────────────────────────────────────────────────────────

def render(grid, gen, paused):
    """Build the full frame as a single string (minimises flicker)."""
    rows, cols = len(grid), len(grid[0])
    pop = population(grid)
    status = "PAUSED" if paused else "RUNNING"
    pause_colour = "\033[1;33m" if paused else "\033[1;32m"

    lines = [CLEAR + CURSOR_HIDE]
    lines.append(
        f"{HEADER_COLOUR}gen: {gen:<6} | population: {pop:<6} "
        f"| status: {pause_colour}{status}{HEADER_COLOUR} "
        f"| [space] pause  [r] random  [g] glider  [q] quit{RESET}"
    )
    lines.append("─" * (cols * 2))

    for row in grid:
        lines.append("".join(f"{CELL_COLOUR}{ALIVE}{RESET}" if cell else DEAD for cell in row))

    lines.append("─" * (cols * 2))
    return "\n".join(lines)


# ── main ────────────────────────────────────────────────────────────────────

def main():
    args = parse_args()

    t_rows, t_cols = term_size()
    rows = min(args.rows, t_rows - 6)
    cols = min(args.cols, (t_cols - 2) // 2)

    if args.glider:
        grid = new_grid(rows, cols)
        place_glider(grid, 0, 0)
    else:
        grid = random_grid(rows, cols, args.density)

    gen = 0
    paused = False
    frame_time = 1.0 / max(args.fps, 1)

    def cleanup(signum, frame):
        sys.stdout.write(CURSOR_SHOW + CLEAR)
        sys.stdout.flush()
        sys.exit(0)

    signal.signal(signal.SIGINT, cleanup)
    signal.signal(signal.SIGTERM, cleanup)

    try:
        with RawInput():
            last_tick = time.monotonic()

            while True:
                ch = RawInput.getch()
                if ch == 'q':
                    break
                elif ch == ' ':
                    paused = not paused
                elif ch == 'r':
                    grid = random_grid(rows, cols, args.density)
                    gen = 0
                elif ch == 'g':
                    grid = new_grid(rows, cols)
                    place_glider(grid, 0, 0)
                    gen = 0

                now = time.monotonic()
                if not paused and now - last_tick >= frame_time:
                    grid = next_gen(grid)
                    gen += 1
                    last_tick = now

                sys.stdout.write(render(grid, gen, paused))
                sys.stdout.flush()

                time.sleep(0.015)

    finally:
        sys.stdout.write(CURSOR_SHOW + CLEAR)
        sys.stdout.flush()


if __name__ == "__main__":
    main()
