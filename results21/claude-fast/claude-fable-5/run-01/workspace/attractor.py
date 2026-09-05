#!/usr/bin/env python3
"""Clifford attractor, rendered as terminal density art and an SVG.

    x' = sin(a*y) + c*cos(a*x)
    y' = sin(b*x) + d*cos(b*y)

Four constants, two lines of math, endless organic shapes.
"""
import math
import random

# A few parameter sets known to produce lovely forms
PRESETS = [
    (-1.4, 1.6, 1.0, 0.7),
    (1.7, 1.7, 0.6, 1.2),
    (-1.7, 1.3, -0.1, -1.2),
    (-1.8, -2.0, -0.5, -0.9),
    (1.5, -1.8, 1.6, 0.9),
]

def iterate(a, b, c, d, n=400_000):
    x, y = 0.1, 0.0
    pts = []
    for i in range(n):
        x, y = (math.sin(a * y) + c * math.cos(a * x),
                math.sin(b * x) + d * math.cos(b * y))
        if i > 100:  # skip transient
            pts.append((x, y))
    return pts

def render_terminal(pts, width=100, height=44):
    xs = [p[0] for p in pts]; ys = [p[1] for p in pts]
    xmin, xmax = min(xs), max(xs)
    ymin, ymax = min(ys), max(ys)
    grid = [[0] * width for _ in range(height)]
    for x, y in pts:
        col = int((x - xmin) / (xmax - xmin) * (width - 1))
        row = int((y - ymin) / (ymax - ymin) * (height - 1))
        grid[row][col] += 1
    peak = max(max(r) for r in grid)
    ramp = " .:-=+*#%@"
    lines = []
    for row in grid:
        line = ""
        for v in row:
            if v == 0:
                line += " "
            else:
                # log scale so faint filaments stay visible
                t = math.log1p(v) / math.log1p(peak)
                line += ramp[min(int(t * (len(ramp) - 1)) + 1, len(ramp) - 1)]
        lines.append(line.rstrip())
    return "\n".join(lines)

def render_svg(pts, path, size=900):
    xs = [p[0] for p in pts]; ys = [p[1] for p in pts]
    xmin, xmax = min(xs), max(xs)
    ymin, ymax = min(ys), max(ys)
    pad = 40
    scale = (size - 2 * pad) / max(xmax - xmin, ymax - ymin)
    with open(path, "w") as f:
        f.write(f'<svg xmlns="http://www.w3.org/2000/svg" width="{size}" height="{size}" '
                f'style="background:#0b0e14">\n')
        # subsample for file size; low opacity so density builds tone
        for x, y in pts[::4]:
            px = pad + (x - xmin) * scale
            py = pad + (y - ymin) * scale
            f.write(f'<circle cx="{px:.1f}" cy="{py:.1f}" r="0.6" '
                    f'fill="#7dd3fc" fill-opacity="0.08"/>\n')
        f.write("</svg>\n")

if __name__ == "__main__":
    a, b, c, d = random.choice(PRESETS)
    pts = iterate(a, b, c, d)
    print(f"Clifford attractor  a={a} b={b} c={c} d={d}\n")
    print(render_terminal(pts))
    render_svg(pts, "/workspace/attractor.svg")
    print(f"\nSVG saved to attractor.svg ({len(pts):,} points)")
