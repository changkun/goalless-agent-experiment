#!/usr/bin/env python3
"""
mandelbrot.py — render the Mandelbrot set in the terminal with truecolor ANSI.

Each character cell stacks two vertical pixels (▀): the foreground color is the
top pixel, the background color is the bottom one, so we get 2x vertical
resolution for free. Iteration counts are mapped through a smooth, cyclic
palette so the bands flow into each other instead of stepping.

Usage:
    python3 mandelbrot.py                 # full set
    python3 mandelbrot.py --zoom seahorse # a named zoom
    python3 mandelbrot.py -W 100 -H 60 --iters 400
"""
from __future__ import annotations
import argparse
import math
import sys

# A few hand-picked vantage points worth looking at.
ZOOMS = {
    "full":      (-0.5,      0.0,       3.2),
    "seahorse":  (-0.745,    0.1135,    0.02),
    "spiral":    (-0.7435,   0.1314,    0.0035),
    "elephant":  ( 0.282,    0.01,      0.06),
    "minibrot":  (-1.7687,   0.0017,    0.012),
}


def smooth_iter(cx: float, cy: float, max_iter: int) -> float | None:
    """Return a fractional escape count, or None for points inside the set."""
    # Cheap interior checks: the main cardioid and the period-2 bulb.
    # These skip the slow inner loop for the largest black regions.
    q = (cx - 0.25) ** 2 + cy * cy
    if q * (q + (cx - 0.25)) <= 0.25 * cy * cy:
        return None
    if (cx + 1.0) ** 2 + cy * cy <= 0.0625:
        return None

    zx = zy = 0.0
    for i in range(max_iter):
        zx2, zy2 = zx * zx, zy * zy
        if zx2 + zy2 > 256.0:  # generous radius -> smoother coloring
            mag = math.sqrt(zx2 + zy2)
            # Normalized iteration count (continuous coloring).
            return i + 1 - math.log(math.log(mag)) / math.log(2)
        zy = 2.0 * zx * zy + cy
        zx = zx2 - zy2 + cx
    return None


def palette(t: float) -> tuple[int, int, int]:
    """Map t in [0,1) to an RGB triple via three offset cosines."""
    a = 2.0 * math.pi
    r = 0.5 + 0.5 * math.cos(a * (t + 0.00))
    g = 0.5 + 0.5 * math.cos(a * (t + 0.33))
    b = 0.5 + 0.5 * math.cos(a * (t + 0.67))
    return int(255 * r), int(255 * g), int(255 * b)


def color_for(esc: float | None, max_iter: int) -> tuple[int, int, int]:
    if esc is None:
        return (0, 0, 0)
    # Compress with a sqrt so the fine detail near the boundary spreads out,
    # then take the fractional part to cycle the palette.
    t = math.sqrt(esc / max_iter) * 3.0
    return palette(t % 1.0)


def render_ascii(cx: float, cy: float, span: float, width: int, height: int,
                 max_iter: int) -> str:
    """Plain-text rendering, one pixel per character — useful for sanity checks."""
    ramp = " .:-=+*#%@"
    aspect = height / width
    half_w, half_h = span / 2.0, span * aspect / 2.0
    out: list[str] = []
    for row in range(height):
        line: list[str] = []
        for col in range(width):
            fx = cx - half_w + (col + 0.5) / width * span
            fy = cy - half_h + (row + 0.5) / height * (2 * half_h)
            esc = smooth_iter(fx, fy, max_iter)
            if esc is None:
                line.append("@")
            else:
                idx = int(math.sqrt(esc / max_iter) * (len(ramp) - 1))
                line.append(ramp[min(idx, len(ramp) - 1)])
        out.append("".join(line))
    return "\n".join(out)


def render(cx: float, cy: float, span: float, width: int, height: int,
           max_iter: int) -> str:
    # `height` is in character rows; we render 2 pixel-rows per character.
    px_h = height * 2
    aspect = px_h / width
    half_w = span / 2.0
    half_h = span * aspect / 2.0

    out: list[str] = []
    for row in range(height):
        line: list[str] = []
        for col in range(width):
            fx = cx - half_w + (col + 0.5) / width * span
            top_y = cy - half_h + (2 * row + 0.5) / px_h * (2 * half_h)
            bot_y = cy - half_h + (2 * row + 1.5) / px_h * (2 * half_h)
            tr, tg, tb = color_for(smooth_iter(fx, top_y, max_iter), max_iter)
            br, bg, bb = color_for(smooth_iter(fx, bot_y, max_iter), max_iter)
            line.append(
                f"\x1b[38;2;{tr};{tg};{tb};48;2;{br};{bg};{bb}m▀"
            )
        line.append("\x1b[0m")
        out.append("".join(line))
    return "\n".join(out)


def main(argv: list[str]) -> int:
    p = argparse.ArgumentParser(description="Truecolor terminal Mandelbrot.")
    p.add_argument("--zoom", choices=sorted(ZOOMS), default="full")
    p.add_argument("-W", "--width", type=int, default=88)
    p.add_argument("-H", "--height", type=int, default=44)
    p.add_argument("--iters", type=int, default=200)
    p.add_argument("--ascii", action="store_true", help="plain-text output")
    args = p.parse_args(argv)

    cx, cy, span = ZOOMS[args.zoom]
    if args.ascii:
        print(render_ascii(cx, cy, span, args.width, args.height, args.iters))
    else:
        print(render(cx, cy, span, args.width, args.height, args.iters))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
