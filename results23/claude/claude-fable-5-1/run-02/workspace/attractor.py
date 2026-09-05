#!/usr/bin/env python3
"""Render a Clifford strange attractor to PNG using only the standard library.

    x' = sin(a*y) + c*cos(a*x)
    y' = sin(b*x) + d*cos(b*y)

Usage: python3 attractor.py [out.png] [iterations]
"""
import math
import struct
import sys
import zlib

W, H = 900, 900
A, B, C, D = [float(v) for v in __import__("os").environ.get("CLIFFORD", "-1.4,1.6,1.0,0.7").split(",")]


def write_png(path, width, height, rgb_rows):
    def chunk(tag, data):
        body = tag + data
        return struct.pack(">I", len(data)) + body + struct.pack(">I", zlib.crc32(body) & 0xFFFFFFFF)

    raw = b"".join(b"\x00" + row for row in rgb_rows)
    png = b"\x89PNG\r\n\x1a\n"
    png += chunk(b"IHDR", struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0))
    png += chunk(b"IDAT", zlib.compress(raw, 9))
    png += chunk(b"IEND", b"")
    with open(path, "wb") as f:
        f.write(png)


def render(iterations):
    counts = [0] * (W * H)
    x = y = 0.1
    # Attractor lives inside |x| <= 1+|c|, |y| <= 1+|d|; add a small margin.
    xr, yr = 1 + abs(C) + 0.1, 1 + abs(D) + 0.1
    sx, sy = (W - 1) / (2 * xr), (H - 1) / (2 * yr)
    sin, cos = math.sin, math.cos
    for _ in range(iterations):
        x, y = sin(A * y) + C * cos(A * x), sin(B * x) + D * cos(B * y)
        px = int((x + xr) * sx)
        py = int((y + yr) * sy)
        counts[py * W + px] += 1

    peak = math.log1p(max(counts))
    rows = []
    for row in range(H):
        buf = bytearray()
        for col in range(W):
            t = math.log1p(counts[row * W + col]) / peak  # 0..1 density
            # Dark navy -> teal -> warm white ramp.
            r = int(255 * min(1.0, 0.05 + 1.6 * t * t))
            g = int(255 * min(1.0, 0.08 + 1.1 * t))
            b = int(255 * min(1.0, 0.20 + 0.9 * math.sqrt(t)))
            buf += bytes((r, g, b))
        rows.append(bytes(buf))
    return rows


if __name__ == "__main__":
    out = sys.argv[1] if len(sys.argv) > 1 else "attractor.png"
    n = int(sys.argv[2]) if len(sys.argv) > 2 else 3_000_000
    write_png(out, W, H, render(n))
    print(f"wrote {out} ({W}x{H}, {n:,} points)")
