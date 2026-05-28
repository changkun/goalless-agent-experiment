#!/usr/bin/env python3
"""
render_png.py — rasterise the flow field straight to a PNG.

Shares the noise + palette machinery with flowfield.py, but instead of emitting
vector paths it plots each streamline into an RGB pixel buffer with additive
alpha blending (so overlapping trails build up light), then encodes a PNG using
only the standard library (zlib for the compressed image data).
"""

from __future__ import annotations

import argparse
import math
import random
import struct
import zlib

from flowfield import PerlinNoise, PALETTES, sample_palette


def _hex_to_rgb(h: str) -> tuple[int, int, int]:
    h = h.lstrip("#")
    return int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)


class Canvas:
    """A flat RGB byte buffer with additive line plotting."""

    def __init__(self, w: int, h: int, bg: tuple[int, int, int]) -> None:
        self.w = w
        self.h = h
        self.buf = bytearray(bg * (w * h))

    def _add(self, x: int, y: int, rgb: tuple[int, int, int], a: float) -> None:
        if 0 <= x < self.w and 0 <= y < self.h:
            i = (y * self.w + x) * 3
            buf = self.buf
            buf[i] = min(255, buf[i] + int(rgb[0] * a))
            buf[i + 1] = min(255, buf[i + 1] + int(rgb[1] * a))
            buf[i + 2] = min(255, buf[i + 2] + int(rgb[2] * a))

    def line(self, x0, y0, x1, y1, rgb, a):
        # Bresenham, plotting additively.
        x0, y0, x1, y1 = int(x0), int(y0), int(x1), int(y1)
        dx = abs(x1 - x0)
        dy = -abs(y1 - y0)
        sx = 1 if x0 < x1 else -1
        sy = 1 if y0 < y1 else -1
        err = dx + dy
        while True:
            self._add(x0, y0, rgb, a)
            if x0 == x1 and y0 == y1:
                break
            e2 = 2 * err
            if e2 >= dy:
                err += dy
                x0 += sx
            if e2 <= dx:
                err += dx
                y0 += sy

    def to_png(self, path: str) -> None:
        # Build raw scanlines, each prefixed with a 0 filter byte.
        raw = bytearray()
        stride = self.w * 3
        for y in range(self.h):
            raw.append(0)
            raw.extend(self.buf[y * stride:(y + 1) * stride])

        def chunk(tag: bytes, data: bytes) -> bytes:
            return (struct.pack(">I", len(data)) + tag + data
                    + struct.pack(">I", zlib.crc32(tag + data) & 0xFFFFFFFF))

        header = struct.pack(">IIBBBBB", self.w, self.h, 8, 2, 0, 0, 0)
        png = (b"\x89PNG\r\n\x1a\n"
               + chunk(b"IHDR", header)
               + chunk(b"IDAT", zlib.compress(bytes(raw), 9))
               + chunk(b"IEND", b""))
        with open(path, "wb") as fh:
            fh.write(png)


def render(width, height, seed, palette_name, out):
    noise = PerlinNoise(seed)
    rng = random.Random(seed ^ 0x9E3779B9)
    stops = PALETTES[palette_name]
    canvas = Canvas(width, height, _hex_to_rgb(sample_palette(stops, 0.0)))

    scale = 0.0022
    step = 2.0
    n_particles = 2600
    max_len = 240

    for _ in range(n_particles):
        x = rng.uniform(0, width)
        y = rng.uniform(0, height)
        tone = (noise.at(x * scale * 2, y * scale * 2) + 1) / 2
        rgb = _hex_to_rgb(sample_palette(stops, 0.25 + 0.75 * tone))
        a = 0.04 + 0.10 * rng.random()
        px, py = x, y
        for _ in range(max_len):
            angle = noise.at(x * scale, y * scale) * math.pi * 2.0
            x += math.cos(angle) * step
            y += math.sin(angle) * step
            if not (0 <= x < width and 0 <= y < height):
                break
            canvas.line(px, py, x, y, rgb, a)
            px, py = x, y

    canvas.to_png(out)
    print(f"wrote {out}  ({width}x{height}, seed={seed}, palette={palette_name})")


def main():
    ap = argparse.ArgumentParser(description="Rasterise flow-field art to PNG.")
    ap.add_argument("--seed", type=int, default=7)
    ap.add_argument("--palette", default="lagoon", choices=sorted(PALETTES))
    ap.add_argument("--out", default="flowfield.png")
    ap.add_argument("--width", type=int, default=900)
    ap.add_argument("--height", type=int, default=600)
    args = ap.parse_args()
    render(args.width, args.height, args.seed, args.palette, args.out)


if __name__ == "__main__":
    main()
