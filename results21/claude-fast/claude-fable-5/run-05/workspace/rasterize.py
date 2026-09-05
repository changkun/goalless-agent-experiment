#!/usr/bin/env python3
"""rasterize.py — render a flowfield seed straight to PNG, zero dependencies.

Reuses flowfield's field/palette logic but draws antialiased-ish strokes
into a pixel buffer and writes the PNG by hand with zlib.

    python3 rasterize.py <seed> [out.png]
"""
import math
import random
import struct
import sys
import zlib

from flowfield import make_noise, PALETTES


def hex_rgb(h):
    h = h.lstrip("#")
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


def render_png(seed, width=900, height=600, n_particles=420, steps=140):
    rng = random.Random(seed)
    angle_noise = make_noise(rng.random(), grid=6)
    turbulence = rng.uniform(2.0, 4.5)
    name, bg, colors = PALETTES[rng.randrange(len(PALETTES))]

    bgr = hex_rgb(bg)
    buf = bytearray(width * height * 3)
    for i in range(0, len(buf), 3):
        buf[i:i + 3] = bytes(bgr)

    def blend(px, py, rgb, alpha):
        if 0 <= px < width and 0 <= py < height:
            i = (py * width + px) * 3
            for c in range(3):
                buf[i + c] = int(buf[i + c] * (1 - alpha) + rgb[c] * alpha)

    def line(x0, y0, x1, y1, rgb, alpha):
        # DDA with soft edges: main pixel full alpha, neighbors half
        n = max(abs(x1 - x0), abs(y1 - y0), 1e-6)
        for t in range(int(n) + 1):
            x = x0 + (x1 - x0) * t / n
            y = y0 + (y1 - y0) * t / n
            blend(int(x), int(y), rgb, alpha)
            blend(int(x) + 1, int(y), rgb, alpha * 0.35)
            blend(int(x), int(y) + 1, rgb, alpha * 0.35)

    strokes = 0
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
            rgb = hex_rgb(rng.choice(colors))
            rng.uniform(0.5, 1.6)  # keep RNG stream aligned with SVG version
            op = rng.uniform(0.25, 0.7)
            for (ax, ay), (bx, by) in zip(pts, pts[1:]):
                line(ax, ay, bx, by, rgb, op)
            strokes += 1

    # --- write PNG ---
    raw = b"".join(
        b"\x00" + bytes(buf[y * width * 3:(y + 1) * width * 3])
        for y in range(height)
    )

    def chunk(tag, data):
        c = tag + data
        return struct.pack(">I", len(data)) + c + struct.pack(">I", zlib.crc32(c))

    png = (
        b"\x89PNG\r\n\x1a\n"
        + chunk(b"IHDR", struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0))
        + chunk(b"IDAT", zlib.compress(raw, 6))
        + chunk(b"IEND", b"")
    )
    return png, name, strokes


def main():
    seed = int(sys.argv[1])
    out = sys.argv[2] if len(sys.argv) > 2 else f"flowfield_{seed}.png"
    png, palette, strokes = render_png(seed)
    with open(out, "wb") as f:
        f.write(png)
    print(f"seed={seed}  palette={palette}  strokes={strokes}  ->  {out}")


if __name__ == "__main__":
    main()
