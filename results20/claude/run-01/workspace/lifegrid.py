#!/usr/bin/env python3
"""lifegrid — Conway's Game of Life in pure ASCII, zero dependencies.

Run:  python3 lifegrid.py
      python3 lifegrid.py --width 80 --height 30 --speed 12 --pattern glider

Keys while running:
    Space    pause / resume
    + / -    faster / slower
    r        randomize
    c        clear the grid
    n        advance one generation (when paused)
    g        load the glider
    G        load the Gosper glider gun
    q        quit
"""
import argparse
import random
import shutil
import sys
import time


# ---------------------------------------------------------------- universe --
def empty_grid(w, h):
    return [[False] * w for _ in range(h)]


def random_grid(w, h, density=0.35):
    return [[random.random() < density for _ in range(w)] for _ in range(h)]


def next_generation(grid):
    h, w = len(grid), len(grid[0])
    nxt = empty_grid(w, h)
    for y in range(h):
        row, up, dn = grid[y], grid[y - 1], grid[(y + 1) % h]
        for x in range(w):
            left, right = row[x - 1], row[(x + 1) % w]
            neighbors = (
                up[x - 1] + up[x] + up[(x + 1) % w] +
                left + right +
                dn[x - 1] + dn[x] + dn[(x + 1) % w]
            )
            alive = row[x]
            nxt[y][x] = neighbors == 3 or (alive and neighbors == 2)
    return nxt


def count_alive(grid):
    return sum(sum(row) for row in grid)


# ------------------------------------------------------------- patterns ------
def _draw(grid, pattern, cx, cy, overwrite=True):
    """Stamp a pattern (list of (x, y) offsets) centred around (cx, cy)."""
    h, w = len(grid), len(grid[0])
    for lx, ly in pattern:
        x, y = cx + lx, cy + ly
        if 0 <= x < w and 0 <= y < h:
            grid[y][x] = not overwrite or True


GLIDER = [(0, 1), (1, 2), (2, 0), (2, 1), (2, 2)]

GUN = [  # Gosper glider gun (offset around a rough centre)
    (24, 0), (22, 1), (24, 1), (12, 2), (13, 2), (20, 2), (21, 2),
    (34, 2), (35, 2), (11, 3), (15, 3), (20, 3), (21, 3), (34, 3), (35, 3),
    (0, 4), (1, 4), (10, 4), (16, 4), (20, 4), (21, 4),
    (0, 5), (1, 5), (10, 5), (14, 5), (16, 5), (17, 5), (22, 5), (24, 5),
    (10, 6), (16, 6), (24, 6), (11, 7), (15, 7), (12, 8), (13, 8),
]


def load_pattern(grid, name):
    h, w = len(grid), len(grid[0])
    cx, cy = w // 2, h // 2
    if name == "glider":
        _draw(grid, GLIDER, cx, cy)
    elif name == "gun":
        _draw(grid, GUN, cx, cy)


# ------------------------------------------------------------- rendering -----
def render(grid, width=None, height=None):
    """Render the grid to text, stripping dead borders where possible."""
    w = width or len(grid[0])
    h = height or len(grid)
    lines = ["".join("█" if c else "·" for c in row[:w]) for row in grid[:h]]
    return "\n".join(lines)


def fit(grid, max_w, max_h):
    """Return the largest achievable (w, h) within the terminal bounds."""
    gw, gh = len(grid[0]), len(grid)
    w = max(8, min(gw, max_w))
    h = max(4, min(gh, max_h))
    return w, h


# ------------------------------------------------------------------- main ----
def main():
    ap = argparse.ArgumentParser(description="Conway's Game of Life in ASCII")
    ap.add_argument("--width", type=int, default=0, help="grid width (default: terminal)")
    ap.add_argument("--height", type=int, default=0, help="grid height (default: terminal)")
    ap.add_argument("--speed", type=float, default=10, help="generations per second (default 10)")
    ap.add_argument("--density", type=float, default=0.35, help="random fill density")
    ap.add_argument("--pattern", choices=["random", "glider", "gun"], default="random")
    args = ap.parse_args()

    # Terminal sizing: double width because glyphs are ~twice as tall as wide.
    tw, th = shutil.get_terminal_size(fallback=(100, 30))
    tw -= 2
    th -= 4
    width = args.width or max(20, min(tw, tw))
    height = args.height or max(12, min(th, th * 2))

    grid = empty_grid(width, height)
    if args.pattern == "glider":
        load_pattern(grid, "glider")
        # place a burst of random cells so it isn't lonely
    elif args.pattern == "gun":
        load_pattern(grid, "gun")
    else:
        grid = random_grid(width, height, args.density)

    paused = True if args.pattern != "random" else False
    delay = 1.0 / max(0.1, args.speed)
    state = render
    gen = 0

    try:
        import termios, tty, select, os

        fd = sys.stdin.fileno()
        raw = False
        try:
            old = termios.tcgetattr(fd)
            tty.setraw(fd)
            raw = True
        except (termios.error, AttributeError, OSError):
            pass  # stdin is a pipe/file — fall back to line-buffered input

        sys.stdout.write("\x1b[?25l")  # hide cursor
        while True:
            sys.stdout.write("\x1b[H")  # home
            sys.stdout.write(render(grid, width, height))
            status = (
                f"\r\x1b[Kgen {gen:>6}   alive {count_alive(grid):>6}   "
                f"[{'||' if paused else '> '}] {args.speed:g}gps   "
                "space=play  +=faster  -=slower  r=rand  c=clear  "
                "n=step  g=glider  G=gun  q=quit"
            )
            sys.stdout.write(status)
            sys.stdout.flush()

            if paused:
                # Wait for a key even when paused.
                r, _, _ = select.select([sys.stdin], [], [], 0.1)
                if not r:
                    continue
            else:
                time.sleep(delay)
                r, _, _ = select.select([sys.stdin], [], [], 0)
                if not r:
                    grid = next_generation(grid)
                    gen += 1
                    continue
            ch = sys.stdin.read(1)

            if ch in (" ",):
                paused = not paused
            elif ch in ("+", "="):
                args.speed = min(60, args.speed + 2)
                delay = 1.0 / args.speed
            elif ch in ("-", "_"):
                args.speed = max(1, args.speed - 2)
                delay = 1.0 / args.speed
            elif ch in ("r",):
                grid = random_grid(width, height, args.density)
                gen = 0
            elif ch in ("c",):
                grid = empty_grid(width, height)
                gen = 0
            elif ch in ("n",):
                if paused:
                    grid = next_generation(grid)
                    gen += 1
            elif ch in ("g",):
                grid = empty_grid(width, height)
                load_pattern(grid, "glider")
                gen = 0
                paused = True
            elif ch in ("G",):
                grid = empty_grid(width, height)
                load_pattern(grid, "gun")
                gen = 0
                paused = True
            elif ch in ("q", "\x03"):
                break

    except (KeyboardInterrupt, EOFError):
        pass
    finally:
        sys.stdout.write("\x1b[?25h")  # show cursor
        if raw:
            try:
                termios.tcsetattr(fd, termios.TCSADRAIN, old)
            except Exception:
                pass
        sys.stdout.write("\r\x1b[K")
        sys.stdout.flush()
        print("bye 👋")


if __name__ == "__main__":
    main()
