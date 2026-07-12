#!/usr/bin/env python3
"""Render the Mandelbrot set as ASCII art in the terminal.

Usage:
    python3 mandelbrot.py [zoom] [center_x] [center_y] [width] [height]

    zoom      -- magnification factor (default 1.0)
    center_x  -- real-axis center    (default -0.5)
    center_y  -- imag-axis center    (default 0.0)
    width     -- character columns   (default 80)
    height    -- character rows      (default 40)
"""
import sys
import colorsys

# Palette: dark -> bright. ' ' is the deep interior, '#' is escaping fast.
RAMP = " .:-=+*#%@"

def mandelbrot(cx: float, cy: float, max_iter: int = 100) -> int:
    """Return escape iteration count for point (cx, cy)."""
    x, y = 0.0, 0.0
    for i in range(max_iter):
        x, y = x * x - y * y + cx, 2.0 * x * y + cy
        if x * x + y * y > 4.0:
            return i
    return max_iter


def render(zoom=1.0, cx=-0.5, cy=0.0, width=80, height=40):
    # Complex plane window. Aspect-corrected for terminal cell shape (~2:1).
    scale = 3.0 / zoom
    step_x = scale / width
    step_y = (scale * 0.5) / height   # 0.5 compensates for tall glyphs
    x0 = cx - scale / 2
    y0 = cy - (scale * 0.5) / 2

    lines = []
    for row in range(height):
        py = y0 + row * step_y
        line = []
        for col in range(width):
            px = x0 + col * step_x
            it = mandelbrot(px, py)
            if it == 100:
                line.append(" ")
            else:
                idx = it * (len(RAMP) - 1) // 100
                line.append(RAMP[idx])
        lines.append("".join(line))
    return "\n".join(lines)


def main():
    args = sys.argv[1:]
    zoom = float(args[0]) if len(args) > 0 else 1.0
    cx = float(args[1]) if len(args) > 1 else -0.5
    cy = float(args[2]) if len(args) > 2 else 0.0
    w = int(args[3]) if len(args) > 3 else 80
    h = int(args[4]) if len(args) > 4 else 40
    print(render(zoom, cx, cy, w, h))


if __name__ == "__main__":
    main()
