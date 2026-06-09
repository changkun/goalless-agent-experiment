#!/usr/bin/env python3
"""A tiny generative garden.

Grows recursive trees with randomized branching and renders them to SVG.
No dependencies — just the standard library.

Usage:
    python3 garden.py [seed]
"""

import math
import random
import sys

W, H = 1200, 700
GROUND = H - 60


def lerp(a, b, t):
    return a + (b - a) * t


def branch_color(depth, max_depth):
    """Trunk fades from dark bark to leafy green as branches thin out."""
    t = depth / max_depth
    r = int(lerp(74, 60, t))
    g = int(lerp(48, 140, t))
    b = int(lerp(34, 60, t))
    return f"rgb({r},{g},{b})"


def grow(rng, x, y, angle, length, width, depth, max_depth, out):
    """Recursively grow a branch; append SVG elements to out."""
    if depth > max_depth or length < 2:
        # A leaf: a small translucent blob of one of a few greens/pinks.
        hue = rng.choice(["#5a9e4b", "#6fae4f", "#8fbf6a", "#c97b9b", "#d9a05b"])
        r = rng.uniform(2.5, 6)
        out.append(
            f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{r:.1f}" '
            f'fill="{hue}" fill-opacity="0.55"/>'
        )
        return

    # Slight upward bias keeps trees from drooping into the ground.
    sway = rng.uniform(-0.12, 0.12)
    nx = x + math.cos(angle + sway) * length
    ny = y - math.sin(angle + sway) * length

    out.append(
        f'<line x1="{x:.1f}" y1="{y:.1f}" x2="{nx:.1f}" y2="{ny:.1f}" '
        f'stroke="{branch_color(depth, max_depth)}" '
        f'stroke-width="{width:.2f}" stroke-linecap="round"/>'
    )

    n_children = 2 if rng.random() < 0.7 else 3
    spread = rng.uniform(0.35, 0.75)
    for i in range(n_children):
        t = i / (n_children - 1) if n_children > 1 else 0.5
        child_angle = angle + lerp(-spread, spread, t) + rng.uniform(-0.15, 0.15)
        child_len = length * rng.uniform(0.65, 0.8)
        grow(rng, nx, ny, child_angle, child_len, width * 0.65,
             depth + 1, max_depth, out)


def tree(rng, x, scale, out):
    max_depth = rng.randint(6, 8)
    grow(rng, x, GROUND, math.pi / 2 + rng.uniform(-0.08, 0.08),
         rng.uniform(70, 110) * scale, rng.uniform(8, 14) * scale,
         0, max_depth, out)


def render(seed):
    rng = random.Random(seed)
    out = []

    # Sky gradient and ground.
    out.append(
        '<defs><linearGradient id="sky" x1="0" y1="0" x2="0" y2="1">'
        '<stop offset="0" stop-color="#1b2a4a"/>'
        '<stop offset="0.7" stop-color="#7a5c7e"/>'
        '<stop offset="1" stop-color="#d98e6a"/>'
        "</linearGradient></defs>"
    )
    out.append(f'<rect width="{W}" height="{H}" fill="url(#sky)"/>')

    # Stars in the upper sky.
    for _ in range(120):
        sx, sy = rng.uniform(0, W), rng.uniform(0, H * 0.5)
        out.append(
            f'<circle cx="{sx:.0f}" cy="{sy:.0f}" r="{rng.uniform(0.4, 1.4):.1f}" '
            f'fill="white" fill-opacity="{rng.uniform(0.3, 0.9):.2f}"/>'
        )

    # A low moon.
    mx = rng.uniform(W * 0.65, W * 0.85)
    out.append(f'<circle cx="{mx:.0f}" cy="120" r="38" fill="#f4ecd6" fill-opacity="0.95"/>')

    out.append(f'<rect y="{GROUND}" width="{W}" height="{H - GROUND}" fill="#23301f"/>')

    # Distant small trees first, larger ones in front.
    positions = sorted(rng.sample(range(80, W - 80), 7))
    for i, px in enumerate(positions):
        scale = lerp(0.45, 1.0, rng.random()) * (0.7 if i % 2 else 1.0)
        tree(rng, px, scale, out)

    # Scattered grass.
    for _ in range(250):
        gx = rng.uniform(0, W)
        gh = rng.uniform(3, 12)
        out.append(
            f'<line x1="{gx:.0f}" y1="{GROUND}" x2="{gx + rng.uniform(-3, 3):.0f}" '
            f'y2="{GROUND - gh:.0f}" stroke="#3a5530" stroke-width="1"/>'
        )

    body = "\n".join(out)
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" '
        f'viewBox="0 0 {W} {H}">\n{body}\n</svg>\n'
    )


if __name__ == "__main__":
    seed = sys.argv[1] if len(sys.argv) > 1 else "dusk"
    svg = render(seed)
    path = f"garden-{seed}.svg"
    with open(path, "w") as f:
        f.write(svg)
    print(f"grew a garden from seed {seed!r} -> {path} ({len(svg)} bytes)")
