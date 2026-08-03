#!/usr/bin/env python3
"""Conway's Game of Life — a minimal, dependency-free terminal implementation.

Run:   python3 game.py            # random soup
       python3 game.py 40 20      # exact grid size (width x height)
       python3 game.py --glider   # start from a small glider pattern

Keys while running (if stdin is a tty):
    Space    pause / resume
    r        reseed random cells
    c        clear the board
    q        quit

Everything is in this one file on purpose — no third-party dependencies.
"""

import os
import random
import sys
import time


# --------------------------------------------------------------------------
# Grid helpers (a board is a set of (col, row) live-cell coordinates)
# --------------------------------------------------------------------------

ALIVE = "█"  # full block
DEAD = " "


def evolve(cells):
    """Return the set of live cells after one generation using the standard rules."""
    counts = {}
    for col, row in cells:
        for dc in (-1, 0, 1):
            for dr in (-1, 0, 1):
                if dc == 0 and dr == 0:
                    continue
                counts[(col + dc, row + dr)] = counts.get((col + dc, row + dr), 0) + 1
    # A cell survives with 2 or 3 neighbours; is born with exactly 3.
    return {
        pos
        for pos, n in counts.items()
        if n == 3 or (n == 2 and pos in cells)
    }


# --------------------------------------------------------------------------
# Rendering
# --------------------------------------------------------------------------

def render(cells, width, height):
    """Render the board to a list of strings (no ANSI codes in the payload)."""
    lines = []
    for row in range(height):
        lines.append(
            "".join(ALIVE if (col, row) in cells else DEAD for col in range(width))
        )
    return lines


def animate(cells, width, height, generations):
    """Draw successive generations to the terminal."""
    try:
        import shutil

        term_w, term_h = shutil.get_terminal_size((80, 24))
        height = min(height, term_h - 2)  # leave a line for the status bar
        width = min(width, term_w)
    except Exception:
        pass

    paused = False
    cells = set(cells)

    for gen in range(generations):
        _clear()
        for line in render(cells, width, height):
            print(line)
        print(f"generation {gen:<6} alive {len(cells):<6}(space) pause  (r) reseed  (c) clear  (q) quit")

        if paused:
            _wait_for_key()  # block until the user presses something to resume

        if os.isatty(sys.stdin.fileno()):
            key = _read_key()
            if key == "q":
                break
            elif key == " ":
                paused = not paused
                continue
            elif key == "r":
                cells = _random_seed(width, height)
                continue
            elif key == "c":
                cells = set()
                continue
        else:
            time.sleep(0.08)

        cells = evolve(cells)


def _clear():
    """Move the cursor home and clear to end of screen (no flicker via full redraw)."""
    sys.stdout.write("\x1b[H\x1b[2J")
    sys.stdout.flush()


def _read_key():
    """Read a single keypress without waiting for Enter."""
    import termios
    import tty

    fd = sys.stdin.fileno()
    old = termios.tcgetattr(fd)
    try:
        tty.setcbreak(fd)
        ch = sys.stdin.read(1)
    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, old)
    return ch


def _wait_for_key():
    _read_key()


# --------------------------------------------------------------------------
# Initial states
# --------------------------------------------------------------------------

def random_seed(width, height, density=0.28):
    rng = random.Random()
    return {
        (c, r)
        for c in range(width)
        for r in range(height)
        if rng.random() < density
    }


def glider_seed(width, height):
    """A classic glider — 5 cells that 'swim' diagonally across the board."""
    glider = {(1, 0), (2, 1), (0, 2), (1, 2), (2, 2)}
    origin = (max(0, (width - 6) // 2), max(0, (height - 6) // 2))
    return {(c + origin[0], r + origin[1]) for c, r in glider}


# --------------------------------------------------------------------------
# CLI
# --------------------------------------------------------------------------

def main(argv):
    width, height = 80, 24
    generations = 10**9

    seed = random_seed
    args = list(argv)
    if "--glider" in args:
        seed = glider_seed
        args.remove("--glider")
    nums = [int(a) for a in args if a.isdigit()]
    if len(nums) >= 2:
        width, height = nums[0], nums[1]

    cells = seed(width, height)
    animate(cells, width, height, generations)
    # Leave the program's own output visible on exit.
    print("\nbye!")


if __name__ == "__main__":
    try:
        main(sys.argv[1:])
    except KeyboardInterrupt:
        sys.exit(0)
    except BrokenPipeError:
        # stdout was closed early (e.g. `game.py | head`). Exit quietly.
        devnull = os.open(os.devnull, os.O_WRONLY)
        os.dup2(devnull, sys.stdout.fileno())
        sys.exit(0)
