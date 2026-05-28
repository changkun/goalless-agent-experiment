#!/usr/bin/env python3
"""
flowfield.py — generative art from a noise-driven flow field.

No third-party dependencies. Implements gradient (Perlin-style) noise from
scratch, seeds a swarm of particles, lets each drift along the angle the noise
field dictates at its position, and records the trail as a smooth SVG polyline.

Usage:
    python3 flowfield.py [--seed N] [--out FILE] [--palette NAME]

Palettes: ember, lagoon, orchid, mono
"""

from __future__ import annotations

import argparse
import math
import random


# --------------------------------------------------------------------------
# Gradient noise (a compact 2D Perlin implementation)
# --------------------------------------------------------------------------
class PerlinNoise:
    """2D Perlin noise with a seeded, shuffled permutation table."""

    def __init__(self, seed: int) -> None:
        rng = random.Random(seed)
        p = list(range(256))
        rng.shuffle(p)
        # Doubled so we can index without wrapping arithmetic.
        self.perm = p + p

    @staticmethod
    def _fade(t: float) -> float:
        # 6t^5 - 15t^4 + 10t^3 — smooth, zero first/second derivatives at ends.
        return t * t * t * (t * (t * 6 - 15) + 10)

    @staticmethod
    def _lerp(a: float, b: float, t: float) -> float:
        return a + t * (b - a)

    @staticmethod
    def _grad(h: int, x: float, y: float) -> float:
        # 8 gradient directions chosen from the hash's low bits.
        h &= 7
        u = x if h < 4 else y
        v = y if h < 4 else x
        return (u if (h & 1) == 0 else -u) + (v if (h & 2) == 0 else -v)

    def at(self, x: float, y: float) -> float:
        """Sample the field at (x, y); returns roughly [-1, 1]."""
        xi = int(math.floor(x)) & 255
        yi = int(math.floor(y)) & 255
        xf = x - math.floor(x)
        yf = y - math.floor(y)

        u = self._fade(xf)
        v = self._fade(yf)

        perm = self.perm
        aa = perm[perm[xi] + yi]
        ab = perm[perm[xi] + yi + 1]
        ba = perm[perm[xi + 1] + yi]
        bb = perm[perm[xi + 1] + yi + 1]

        x1 = self._lerp(self._grad(aa, xf, yf), self._grad(ba, xf - 1, yf), u)
        x2 = self._lerp(self._grad(ab, xf, yf - 1), self._grad(bb, xf - 1, yf - 1), u)
        return self._lerp(x1, x2, v)


# --------------------------------------------------------------------------
# Colour palettes — each is a list of (r, g, b) stops we interpolate across.
# --------------------------------------------------------------------------
PALETTES = {
    "ember":  [(20, 12, 28), (120, 28, 48), (224, 96, 52), (247, 196, 110)],
    "lagoon": [(8, 24, 38), (16, 78, 102), (44, 168, 168), (180, 234, 214)],
    "orchid": [(18, 10, 34), (78, 32, 110), (176, 70, 168), (244, 178, 220)],
    "mono":   [(14, 14, 16), (78, 80, 88), (160, 164, 172), (236, 238, 242)],
}


def sample_palette(stops: list[tuple[int, int, int]], t: float) -> str:
    """Map t in [0, 1] to a hex colour interpolated across the stops."""
    t = max(0.0, min(1.0, t))
    span = len(stops) - 1
    pos = t * span
    i = min(int(pos), span - 1)
    f = pos - i
    a, b = stops[i], stops[i + 1]
    r = round(a[0] + (b[0] - a[0]) * f)
    g = round(a[1] + (b[1] - a[1]) * f)
    bl = round(a[2] + (b[2] - a[2]) * f)
    return f"#{r:02x}{g:02x}{bl:02x}"


# --------------------------------------------------------------------------
# Flow field tracing
# --------------------------------------------------------------------------
def trace(width: int, height: int, seed: int, palette_name: str) -> str:
    noise = PerlinNoise(seed)
    rng = random.Random(seed ^ 0x9E3779B9)
    stops = PALETTES[palette_name]

    scale = 0.0022      # how zoomed-in the noise is (smaller = broader sweeps)
    step = 2.4          # distance advanced per integration step
    n_particles = 1400
    max_len = 220       # max steps before a particle retires

    paths: list[str] = []

    for _ in range(n_particles):
        x = rng.uniform(0, width)
        y = rng.uniform(0, height)
        # Colour each streamline by where it starts in the field.
        tone = (noise.at(x * scale * 2, y * scale * 2) + 1) / 2
        colour = sample_palette(stops, tone)
        # Vary opacity and weight so layers read as depth.
        opacity = 0.10 + 0.32 * rng.random()
        weight = 0.6 + 1.6 * rng.random()

        pts = [(x, y)]
        for _ in range(max_len):
            angle = noise.at(x * scale, y * scale) * math.pi * 2.0
            x += math.cos(angle) * step
            y += math.sin(angle) * step
            if not (0 <= x < width and 0 <= y < height):
                break
            pts.append((x, y))

        if len(pts) < 4:
            continue

        d = "M" + " L".join(f"{px:.1f},{py:.1f}" for px, py in pts)
        paths.append(
            f'<path d="{d}" fill="none" stroke="{colour}" '
            f'stroke-width="{weight:.2f}" stroke-opacity="{opacity:.2f}" '
            f'stroke-linecap="round"/>'
        )

    bg = sample_palette(stops, 0.0)
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" '
        f'height="{height}" viewBox="0 0 {width} {height}">\n'
        f'<rect width="{width}" height="{height}" fill="{bg}"/>\n'
        + "\n".join(paths)
        + "\n</svg>\n"
    )


def main() -> None:
    ap = argparse.ArgumentParser(description="Generative flow-field art -> SVG.")
    ap.add_argument("--seed", type=int, default=7, help="random seed")
    ap.add_argument("--out", default="flowfield.svg", help="output SVG path")
    ap.add_argument("--palette", default="lagoon", choices=sorted(PALETTES),
                    help="colour palette")
    ap.add_argument("--width", type=int, default=1200)
    ap.add_argument("--height", type=int, default=800)
    args = ap.parse_args()

    svg = trace(args.width, args.height, args.seed, args.palette)
    with open(args.out, "w") as fh:
        fh.write(svg)
    print(f"wrote {args.out}  ({len(svg) // 1024} KB, "
          f"seed={args.seed}, palette={args.palette})")


if __name__ == "__main__":
    main()
