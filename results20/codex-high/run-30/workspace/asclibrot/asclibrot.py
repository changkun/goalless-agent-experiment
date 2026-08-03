#!/usr/bin/env python3
"""asclibrot — render the Mandelbrot set as animated ASCII art in your terminal."""

from __future__ import annotations

import argparse
import math
import os
import sys
import time


# ASCII ramp, darkest -> brightest (space sorts before '#' and '.').
RAMP = " .:-=+*#%@"


def shade(steps: int) -> str:
    """Map 0..iterations to an ASCII character."""
    if steps >= len(RAMP):
        return RAMP[-1]            # inside the set, brightest block
    return RAMP[steps]


def mandel(cre: float, cim: float, max_iter: int) -> int:
    """Return iteration count for point c = cre + cim*i in the Mandelbrot set."""
    zre = zim = 0.0
    for n in range(max_iter):
        zre2, zim2 = zre * zre, zim * zim
        if zre2 + zim2 > 4.0:
            return n
        zim = 2.0 * zre * zim + cim
        zre = zre2 - zim2 + cre
    return max_iter


def frame(width: int, height: int, center: complex, scale: float, max_iter: int) -> list[str]:
    """Render one frame, returning a list of strings (one per row)."""
    rows: list[str] = []
    y0 = center.imag + scale / 2.0
    y_step = scale / height
    x_step = scale * (width / height) / width
    x0 = center.real - (x_step * width) / 2.0

    for row in range(height):
        line_chars = []
        y = y0 - row * y_step
        for col in range(width):
            x = x0 + col * x_step
            line_chars.append(shade(mandel(x, y, max_iter)))
        rows.append("".join(line_chars))
    return rows


def animate(width: int, height: int, zoom_factor: float, steps: int, max_iter: int, fps: float) -> None:
    """Zoom toward a coastal feature of the set, animating in place."""
    center = complex(-0.743643887037151, 0.131825904205330)
    scale = 3.0
    delay = 1.0 / fps
    hide = "\x1b[?25l"   # hide cursor
    show = "\x1b[?25h"   # show cursor
    sys.stdout.write(hide)
    try:
        prev = 0.0
        for i in range(steps):
            scaled = scale * (zoom_factor ** i)
            it = min(max_iter, int(100 * (1 + i * 0.5)))
            sys.stdout.write("\x1b[H")   # home cursor
            sys.stdout.write("\n".join(frame(width, height, center, scaled, it)))
            sys.stdout.write(f"\n  zoom depth {i + 1}/{steps}   iterations {it}")
            sys.stdout.flush()
            time.sleep(delay)
            prev = scaled
    finally:
        sys.stdout.write(show)
        sys.stdout.flush()


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="mode", required=True)

    still = sub.add_parser("still", help="render a single static frame")
    still.add_argument("--width", type=int, default=shutil_term_width())
    still.add_argument("--height", type=int, default=30)
    still.add_argument("--center", default="-0.5,0.0")
    still.add_argument("--scale", type=float, default=3.0)
    still.add_argument("--iterations", type=int, default=80)

    anim = sub.add_parser("animate", help="animate a smooth zoom into the set")
    anim.add_argument("--width", type=int, default=shutil_term_width())
    anim.add_argument("--height", type=int, default=30)
    anim.add_argument("--zoom-factor", type=float, default=1.06)
    anim.add_argument("--steps", type=int, default=60)
    anim.add_argument("--iterations", type=int, default=120)
    anim.add_argument("--fps", type=float, default=12.0)

    args = parser.parse_args(argv)

    if args.mode == "animate":
        animate(args.width, args.height, args.zoom_factor, args.steps,
                args.iterations, args.fps)
    else:
        cre, cim = map(float, args.center.split(","))
        for line in frame(args.width, args.height, complex(cre, cim), args.scale, args.iterations):
            print(line)
    return 0


def shutil_term_width() -> int:
    """Best-effort terminal width; fall back to 80."""
    try:
        import shutil
        return shutil.get_terminal_size((80, 24)).columns
    except Exception:
        return 80


if __name__ == "__main__":
    sys.exit(main())
