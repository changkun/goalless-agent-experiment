#!/usr/bin/env python3
"""
DOOM fire — the classic PSX/Nintendo DOOM fire effect, in your terminal.

The algorithm is beautifully simple:
  1. The bottom row of the buffer is a heat source, pinned to max intensity.
  2. Each frame, every pixel takes the intensity of the pixel below it,
     minus a small random decay, and spreads it upward (with a little
     horizontal jitter to make the flames lick sideways).
  3. Intensity maps onto a palette: black -> red -> orange -> yellow -> white.

Rendering uses the upper-half-block character '▀' with truecolor ANSI codes:
the foreground colors the top pixel of the cell, the background the bottom
pixel — so every character cell shows two vertical pixels of fire.

Run it live:        python3 fire.py
Render N frames:    python3 fire.py --frames 30
Snapshot one frame: python3 fire.py --snapshot
"""

import argparse
import os
import random
import sys
import time

# The DOOM fire palette: 37 intensities from cold black to hot white.
# Built from the original's RGB ramps.
PALETTE = []
_stops = [
    (0, 0, 0),        # black
    (31, 7, 7),       # deep ember
    (71, 15, 7),      # dark red
    (119, 31, 7),     # red
    (167, 47, 7),     # orange-red
    (199, 79, 15),    # orange
    (223, 119, 15),   # bright orange
    (223, 159, 15),   # gold
    (239, 199, 39),   # yellow
    (255, 255, 111),  # pale yellow
    (255, 255, 255),  # white-hot
]
for i in range(len(_stops) - 1):
    a, b = _stops[i], _stops[i + 1]
    steps = 37 // (len(_stops) - 1)
    for t in range(steps):
        f = t / steps
        PALETTE.append(tuple(int(a[c] + (b[c] - a[c]) * f) for c in range(3)))
while len(PALETTE) < 37:  # top up to exactly 37 with white
    PALETTE.append((255, 255, 255))
MAX_HEAT = len(PALETTE) - 1


def terminal_size():
    try:
        cols, rows = os.get_terminal_size()
    except OSError:
        cols, rows = 80, 24
    return cols, rows


def spread_fire(fire, width, height):
    """One propagation step: heat rises, decays, and jitters sideways."""
    for x in range(width):
        for y in range(1, height):
            src = y * width + x
            decay = random.randint(0, 3)
            drift = random.randint(0, 3) - 1  # -1, 0, or +1 column
            dst_x = (x + drift) % width
            dst = (y - 1) * width + dst_x
            fire[dst] = max(0, fire[src] - decay)


def render(fire, width, height):
    """Render the buffer as ANSI truecolor half-blocks. Returns a string."""
    out = ["\x1b[H"]  # move cursor home (no flicker, no full clear)
    for row in range(0, height - 1, 2):
        line = []
        for x in range(width):
            top = PALETTE[fire[row * width + x]]
            bot = PALETTE[fire[(row + 1) * width + x]]
            line.append(f"\x1b[38;2;{top[0]};{top[1]};{top[2]}m"
                        f"\x1b[48;2;{bot[0]};{bot[1]};{bot[2]}m▀")
        line.append("\x1b[0m")
        out.append("".join(line))
    return "\n".join(out)


def run(frames=None, width=None, height=None, snapshot=False, seed=None):
    if seed is not None:
        random.seed(seed)
    cols, rows = terminal_size()
    w = width or cols
    h = height or (rows * 2)  # two pixels per character row

    fire = [0] * (w * h)
    # Ignite the heat source along the bottom row.
    for x in range(w):
        fire[(h - 1) * w + x] = MAX_HEAT

    sys.stdout.write("\x1b[2J\x1b[?25l")  # clear screen, hide cursor
    try:
        n = 0
        while frames is None or n < frames:
            spread_fire(fire, w, h)
            sys.stdout.write(render(fire, w, h))
            sys.stdout.flush()
            n += 1
            if frames is None:
                time.sleep(1 / 30)
        if snapshot:
            # Let it burn a while first so the flames are fully developed.
            for _ in range(60):
                spread_fire(fire, w, h)
            sys.stdout.write(render(fire, w, h))
            sys.stdout.flush()
    except KeyboardInterrupt:
        pass
    finally:
        sys.stdout.write("\x1b[0m\x1b[?25h\n")  # reset colors, show cursor


def main():
    p = argparse.ArgumentParser(description="DOOM fire, in your terminal.")
    p.add_argument("--frames", type=int, default=None,
                   help="render exactly N frames then exit (default: loop forever)")
    p.add_argument("--width", type=int, default=None, help="fire width in pixels")
    p.add_argument("--height", type=int, default=None, help="fire height in pixels")
    p.add_argument("--snapshot", action="store_true",
                   help="burn in for 60 steps, print one frame, exit")
    p.add_argument("--seed", type=int, default=None, help="RNG seed for reproducible flames")
    args = p.parse_args()
    if args.snapshot:
        run(frames=0, width=args.width, height=args.height,
            snapshot=True, seed=args.seed)
    else:
        run(frames=args.frames, width=args.width, height=args.height, seed=args.seed)


if __name__ == "__main__":
    main()
