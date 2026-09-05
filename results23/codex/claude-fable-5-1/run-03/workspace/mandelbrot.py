#!/usr/bin/env python3
"""Render the Mandelbrot set as ASCII art in the terminal.

Usage:
    python3 mandelbrot.py [--width N] [--height N] [--iterations N]
                          [--center RE IM] [--zoom Z]
"""

import argparse
import shutil

PALETTE = " .:-=+*#%@"


def escape_time(real, imag, max_iterations):
    """Return how many iterations it takes for the point to escape."""
    z_real = 0.0
    z_imag = 0.0
    for step in range(max_iterations):
        z_real, z_imag = (
            z_real * z_real - z_imag * z_imag + real,
            2.0 * z_real * z_imag + imag,
        )
        if z_real * z_real + z_imag * z_imag > 4.0:
            return step
    return max_iterations


def render(width, height, max_iterations, center_real, center_imag, zoom):
    """Return the rendered frame as a list of strings, one per row."""
    span_real = 3.5 / zoom
    span_imag = span_real * (height / width) * 2.0
    rows = []
    for row in range(height):
        imag = center_imag + span_imag * (0.5 - row / height)
        line = []
        for column in range(width):
            real = center_real + span_real * (column / width - 0.5)
            steps = escape_time(real, imag, max_iterations)
            if steps == max_iterations:
                line.append(" ")
            else:
                line.append(PALETTE[steps % len(PALETTE)])
        rows.append("".join(line))
    return rows


def main():
    terminal = shutil.get_terminal_size(fallback=(80, 24))
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--width", type=int, default=terminal.columns)
    parser.add_argument("--height", type=int, default=max(terminal.lines - 1, 10))
    parser.add_argument("--iterations", type=int, default=60)
    parser.add_argument(
        "--center", type=float, nargs=2, default=(-0.75, 0.0), metavar=("RE", "IM")
    )
    parser.add_argument("--zoom", type=float, default=1.0)
    args = parser.parse_args()

    frame = render(
        args.width, args.height, args.iterations, args.center[0], args.center[1], args.zoom
    )
    print("\n".join(frame))


if __name__ == "__main__":
    main()
