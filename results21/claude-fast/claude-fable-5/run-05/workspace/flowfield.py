#!/usr/bin/env python3
"""flowfield.py — generative flow-field art, zero dependencies.

Drops particles onto a 2D value-noise field and lets each one wander
downstream, tracing its path as a polyline. Output is an SVG.

    python3 flowfield.py [seed]
"""
import math
import random
import sys

# ---------------------------------------------------------------- noise

def make_noise(seed, grid=8):
    """Smooth 2D value noise: random values on a lattice, cosine-blended."""
    rng = random.Random(seed)
    lattice = [[rng.uniform(0, 1) for _ in range(grid + 2)] for _ in range(grid + 2)]

    def smooth(t):
        return (1 - math.cos(t * math.pi)) / 2

    def noise(x, y):
        # x, y in [0, 1); scale to lattice space
        gx, gy = x * grid, y * grid
        ix, iy = int(gx), int(gy)
        fx, fy = smooth(gx - ix), smooth(gy - iy)
        a = lattice[iy][ix]
        b = lattice[iy][ix + 1]
        c = lattice[iy + 1][ix]
        d = lattice[iy + 1][ix + 1]
        return (a * (1 - fx) + b * fx) * (1 - fy) + (c * (1 - fx) + d * fx) * fy

    return noise

# ---------------------------------------------------------------- palette

PALETTES = [
    ("dusk",    "#1a1a2e", ["#e94560", "#f5a623", "#f8e9a1", "#a8dadc"]),
    ("tide",    "#0b132b", ["#5bc0be", "#6fffe9", "#3a506b", "#fffffa"]),
    ("ember",   "#161210", ["#ff6d00", "#ffab40", "#ffd180", "#8d6e63"]),
    ("moss",    "#10140f", ["#a3b18a", "#dad7cd", "#588157", "#e9edc9"]),
    ("orchid",  "#1d1128", ["#c77dff", "#e0aaff", "#7b2cbf", "#ffd6ff"]),
]

# ---------------------------------------------------------------- render

def render(seed, width=900, height=600, n_particles=420, steps=140):
    rng = random.Random(seed)
    angle_noise = make_noise(rng.random(), grid=6)
    turbulence = rng.uniform(2.0, 4.5)          # how twisty the field is
    name, bg, colors = PALETTES[rng.randrange(len(PALETTES))]

    paths = []
    for _ in range(n_particles):
        x, y = rng.uniform(0, width), rng.uniform(0, height)
        pts = [(x, y)]
        for _ in range(steps):
            a = angle_noise(x / width, y / height) * math.tau * turbulence
            x += math.cos(a) * 2.4
            y += math.sin(a) * 2.4
            if not (0 <= x < width and 0 <= y < height):
                break
            pts.append((x, y))
        if len(pts) > 8:
            color = rng.choice(colors)
            w = rng.uniform(0.5, 1.6)
            op = rng.uniform(0.25, 0.7)
            d = " ".join(f"{px:.1f},{py:.1f}" for px, py in pts)
            paths.append(
                f'<polyline points="{d}" fill="none" stroke="{color}" '
                f'stroke-width="{w:.2f}" stroke-opacity="{op:.2f}" '
                f'stroke-linecap="round"/>'
            )

    svg = (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" '
        f'viewBox="0 0 {width} {height}">\n'
        f'<rect width="{width}" height="{height}" fill="{bg}"/>\n'
        + "\n".join(paths)
        + "\n</svg>\n"
    )
    return svg, name, len(paths)


def main():
    seed = int(sys.argv[1]) if len(sys.argv) > 1 else random.randrange(10**6)
    svg, palette, n = render(seed)
    out = f"flowfield_{seed}.svg"
    with open(out, "w") as f:
        f.write(svg)
    print(f"seed={seed}  palette={palette}  strokes={n}  ->  {out}")


if __name__ == "__main__":
    main()
