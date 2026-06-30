#!/usr/bin/env python3
"""Mandelbrot set renderer — terminal edition."""

import os
import sys

def mandelbrot(c, max_iter=80):
    z = 0
    for n in range(max_iter):
        if abs(z) > 2:
            return n
        z = z * z + c
    return max_iter

def render(width=120, height=40, cx=-0.5, cy=0, zoom=1.5):
    # ANSI 256-color gradient palette (blues → purples → golds → white → black)
    palette = [
        16, 17, 18, 19, 20, 21, 27, 33, 39, 45, 51,
        87, 123, 159, 195, 231, 230, 229, 228, 227, 226,
        220, 214, 208, 202, 196, 160, 124, 88, 52, 53, 54,
        55, 56, 57, 63, 69, 75, 81, 117, 153, 189, 225, 231,
    ]
    max_iter = len(palette)

    rows = []
    for row in range(height):
        line = []
        for col in range(width):
            # map pixel to complex plane
            real = cx + (col - width  / 2) * (zoom * 3.5 / width)
            imag = cy + (row - height / 2) * (zoom * 2.0 / height)
            c = complex(real, imag)
            n = mandelbrot(c, max_iter)
            if n == max_iter:
                line.append("\x1b[48;5;16m  \x1b[0m")  # inside = black
            else:
                color = palette[n % len(palette)]
                line.append(f"\x1b[48;5;{color}m  \x1b[0m")
        rows.append("".join(line))

    return "\n".join(rows)

def main():
    # A few iconic views
    views = [
        dict(name="Classic full set",    cx=-0.5,      cy=0.0,      zoom=1.3),
        dict(name="Seahorse valley",     cx=-0.7269,   cy=0.1889,   zoom=0.003),
        dict(name="Lightning bolt",      cx=-0.1592,   cy=-1.0317,  zoom=0.01),
        dict(name="Elephant valley",     cx=0.3,       cy=0.0,      zoom=0.08),
    ]

    for i, view in enumerate(views):
        os.system("clear")
        print(f"\x1b[1m  {view['name']}\x1b[0m")
        print()
        frame = render(cx=view["cx"], cy=view["cy"], zoom=view["zoom"])
        print(frame)
        print()
        if i < len(views) - 1:
            try:
                input("  \x1b[2m[press Enter for next view]\x1b[0m  ")
            except (EOFError, KeyboardInterrupt):
                print()
                sys.exit(0)

    print("\x1b[2m  Done.\x1b[0m\n")

if __name__ == "__main__":
    main()
