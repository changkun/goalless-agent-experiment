#!/usr/bin/env python3
"""mandelbrot.py — render the Mandelbrot set to the terminal, pure stdlib.

A tiny, self-contained escape-time fractal renderer. No dependencies beyond
the standard library. Draws the classic Mandelbrot set as ANSI half-block
"pixels" for 2x density, with an ASCII art palette when ANSI is unavailable.

Usage:
    python3 mandelbrot.py                 # default view
    python3 mandelbrot.py --zoom 0.5      # zoom factor (smaller = deeper)
    python3 mandelbrot.py --x -0.7269 --y 0.1889 --zoom 500000   # "spiral" deep zoom
    python3 mandelbrot.py --plain         # ANSI off (ASCII-only output)
"""

import argparse
import sys

# Consecutive characters approximate escape-time bands from cool (near set)
# to warm (far). Dark-on-light ordering: .,:;=+*#%@ is the classic ramp.
PALETTE = " .:-=+*#%@"
N_SHADES = len(PALETTE)


def escape_time(c_real, c_imag, max_iter):
    """Return iteration count at which z=z^2+c escapes radius 2 (else max_iter)."""
    z_real = 0.0
    z_imag = 0.0
    # |z|^2 > 4 means |z| > 2, outside the set.
    for i in range(max_iter):
        # z^2 = (a+bi)^2 = (a^2-b^2) + (2ab)i
        r2 = z_real * z_real
        i2 = z_imag * z_imag
        if r2 + i2 > 4.0:
            return i
        z_imag = 2.0 * z_real * z_imag + c_imag
        z_real = r2 - i2 + c_real
    return max_iter


def render(width, height, x_min, x_max, y_min, y_max, max_iter):
    """Compute a 2D array of escape times over the view rectangle."""
    cols = []
    step_x = (x_max - x_min) / width
    row = 0
    while row < height:
        c_imag = y_min + row * (y_max - y_min) / height
        line = []
        col = 0
        while col < width:
            c_real = x_min + col * step_x
            line.append(escape_time(c_real, c_imag, max_iter))
            col += 1
        cols.append(line)
        row += 1
    return cols


def shade(iter_count, max_iter):
    """Map an escape time to a palette index (high near set -> bright char)."""
    if iter_count >= max_iter:
        return N_SHADES - 1          # inside the set
    # Log-scaled so the fine structure near the boundary stays visible.
    t = (iter_count / max_iter) ** 0.35
    return int(t * (N_SHADES - 1))


def emit(grid, max_iter, use_ansi):
    cols = len(grid[0])
    out = []
    for line in grid:
        row_chars = []
        for c in line:
            if use_ansi:
                idx = shade(c, max_iter)
                # 16-color terminal: map palette index into an intensity ramp,
                # printing a UTF-8 lower half-block for 2:1 vertical density.
                if c >= max_iter:
                    color = 255  # white for the set itself
                else:
                    # cycle through a blue->magenta->yellow gradient by iter count
                    color = (16 + 36 * (idx % 3) + 6 * ((idx // 3) % 3) + (idx % 6))
                row_chars.append(f"\x1b[48;5;{color}m▀")
            else:
                row_chars.append(PALETTE[shade(c, max_iter)])
        row = "".join(row_chars)
        if use_ansi:
            row += "\x1b[0m"
        out.append(row)
    return "\n".join(out)


def main():
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--width", type=int, default=100, help="columns")
    parser.add_argument("--height", type=int, default=40, help="rows")
    parser.add_argument("--iter", dest="max_iter", type=int, default=800,
                        help="max iterations")
    parser.add_argument("--x", type=float, default=-0.5, help="center real")
    parser.add_argument("--y", type=float, default=0.0, help="center imag")
    parser.add_argument("--zoom", type=float, default=1.0,
                        help="zoom factor (higher = more zoomed in)")
    parser.add_argument("--plain", action="store_true",
                        help="disable ANSI color")
    args = parser.parse_args()

    # Full set spans roughly [-2.5, 1.0] x [-1.25, 1.25]. Zoom shrinks the
    # window about the chosen center; aspect-correct the y extent.
    span_x = 3.5 / args.zoom
    aspect = args.height / args.width
    span_y = span_x * aspect
    x_min, x_max = args.x - span_x / 2, args.x + span_x / 2
    y_min, y_max = args.y - span_y / 2, args.y + span_y / 2

    use_ansi = (not args.plain) and sys.stdout.isatty()
    if not sys.stdout.isatty() and not args.plain:
        print("(piped output: ANSI disabled, plain ASCII shown)\n", file=sys.stderr)

    grid = render(args.width, args.height, x_min, x_max, y_min, y_max,
                  args.max_iter)
    print(emit(grid, args.max_iter, use_ansi))


if __name__ == "__main__":
    main()
