#!/usr/bin/env python3
"""Discover and render a chaotic Clifford attractor.

Randomly samples parameters (a, b, c, d) for the map

    x' = sin(a*y) + c*cos(a*x)
    y' = sin(b*x) + d*cos(b*y)

keeps only parameter sets whose largest Lyapunov exponent is positive
(i.e. genuinely chaotic, not a fixed point or limit cycle), then renders
the orbit as Unicode braille dots in the terminal and as an SVG file.

Usage: python3 attractor.py [seed]
"""

import math
import random
import sys


def step(x, y, a, b, c, d):
    return math.sin(a * y) + c * math.cos(a * x), \
           math.sin(b * x) + d * math.cos(b * y)


def lyapunov(a, b, c, d, n=2000):
    """Estimate the largest Lyapunov exponent by tracking a nearby orbit."""
    x, y = 0.1, 0.1
    for _ in range(100):  # settle onto the attractor
        x, y = step(x, y, a, b, c, d)
    eps = 1e-8
    x2, y2 = x + eps, y
    total = 0.0
    for _ in range(n):
        x, y = step(x, y, a, b, c, d)
        x2, y2 = step(x2, y2, a, b, c, d)
        dx, dy = x2 - x, y2 - y
        dist = math.hypot(dx, dy)
        if dist == 0 or not math.isfinite(dist):
            return -math.inf
        total += math.log(dist / eps)
        # renormalize the perturbed orbit back to distance eps
        x2, y2 = x + dx * eps / dist, y + dy * eps / dist
    return total / n


def find_chaotic(rng):
    while True:
        a, b, c, d = (rng.uniform(-2.5, 2.5) for _ in range(4))
        lam = lyapunov(a, b, c, d)
        if lam > 0.05:  # clearly chaotic
            return a, b, c, d, lam


def orbit(a, b, c, d, n):
    x, y = 0.1, 0.1
    for _ in range(100):
        x, y = step(x, y, a, b, c, d)
    pts = []
    for _ in range(n):
        x, y = step(x, y, a, b, c, d)
        pts.append((x, y))
    return pts


def render_braille(pts, cols=76, rows=30):
    """Each terminal cell is a 2x4 grid of braille dots."""
    w, h = cols * 2, rows * 4
    xs = [p[0] for p in pts]
    ys = [p[1] for p in pts]
    xmin, xmax, ymin, ymax = min(xs), max(xs), min(ys), max(ys)
    pad_x = (xmax - xmin) * 0.04
    pad_y = (ymax - ymin) * 0.04
    xmin, xmax = xmin - pad_x, xmax + pad_x
    ymin, ymax = ymin - pad_y, ymax + pad_y

    grid = [[0] * cols for _ in range(rows)]
    # braille dot bit values by (col within cell, row within cell)
    bits = [[0x01, 0x08], [0x02, 0x10], [0x04, 0x20], [0x40, 0x80]]
    for x, y in pts:
        px = int((x - xmin) / (xmax - xmin) * (w - 1))
        py = int((ymax - y) / (ymax - ymin) * (h - 1))  # flip y for screen
        grid[py // 4][px // 2] |= bits[py % 4][px % 2]

    return "\n".join(
        "".join(chr(0x2800 + cell) if cell else " " for cell in row)
        for row in grid
    )


def render_svg(pts, path, size=1000):
    xs = [p[0] for p in pts]
    ys = [p[1] for p in pts]
    xmin, xmax, ymin, ymax = min(xs), max(xs), min(ys), max(ys)
    span = max(xmax - xmin, ymax - ymin) * 1.08
    cx, cy = (xmin + xmax) / 2, (ymin + ymax) / 2

    def sx(x):
        return (x - cx) / span * size + size / 2

    def sy(y):
        return (cy - y) / span * size + size / 2

    circles = "\n".join(
        f'<circle cx="{sx(x):.1f}" cy="{sy(y):.1f}" r="0.6"/>'
        for x, y in pts
    )
    svg = (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{size}" height="{size}" '
        f'viewBox="0 0 {size} {size}">\n'
        f'<rect width="100%" height="100%" fill="#0b0e14"/>\n'
        f'<g fill="#7fd4ff" fill-opacity="0.35">\n{circles}\n</g>\n</svg>\n'
    )
    with open(path, "w") as f:
        f.write(svg)


def main():
    seed = int(sys.argv[1]) if len(sys.argv) > 1 else random.randrange(10**6)
    rng = random.Random(seed)
    a, b, c, d, lam = find_chaotic(rng)
    pts = orbit(a, b, c, d, 60000)

    print(render_braille(pts))
    print()
    print(f"seed={seed}  a={a:+.4f} b={b:+.4f} c={c:+.4f} d={d:+.4f}  "
          f"Lyapunov ≈ {lam:.3f}")
    render_svg(pts, "/workspace/attractor.svg")
    print("high-res version saved to /workspace/attractor.svg")


if __name__ == "__main__":
    main()
