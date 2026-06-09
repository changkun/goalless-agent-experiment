#!/usr/bin/env python3
"""Micro-rasterizer for the SVG subset emitted by garden.py.

Understands: one vertical linear gradient rect, plain rects, lines with
stroke-width/linecap=round, and circles with fill-opacity. Writes a PNG
using only the standard library.

Usage:
    python3 rasterize.py garden-dusk.svg [out.png]
"""

import re
import struct
import sys
import zlib


def parse_color(s):
    if s.startswith("rgb("):
        return tuple(int(v) for v in s[4:-1].split(","))
    if s.startswith("#") and len(s) == 7:
        return tuple(int(s[i:i + 2], 16) for i in (1, 3, 5))
    return {"white": (255, 255, 255)}.get(s, (0, 0, 0))


class Canvas:
    def __init__(self, w, h):
        self.w, self.h = w, h
        self.px = bytearray(w * h * 3)

    def blend(self, x, y, color, alpha):
        if 0 <= x < self.w and 0 <= y < self.h:
            i = (y * self.w + x) * 3
            for c in range(3):
                old = self.px[i + c]
                self.px[i + c] = int(old + (color[c] - old) * alpha)

    def fill_rect(self, x0, y0, w, h, color):
        for y in range(max(0, int(y0)), min(self.h, int(y0 + h))):
            for x in range(max(0, int(x0)), min(self.w, int(x0 + w))):
                i = (y * self.w + x) * 3
                self.px[i:i + 3] = bytes(color)

    def gradient_rect(self, stops):
        """Vertical gradient over the whole canvas."""
        for y in range(self.h):
            t = y / (self.h - 1)
            # Find surrounding stops.
            for (o0, c0), (o1, c1) in zip(stops, stops[1:]):
                if o0 <= t <= o1:
                    f = (t - o0) / (o1 - o0) if o1 > o0 else 0
                    color = bytes(int(c0[k] + (c1[k] - c0[k]) * f) for k in range(3))
                    break
            else:
                color = bytes(stops[-1][1])
            row = color * self.w
            self.px[y * self.w * 3:(y + 1) * self.w * 3] = row

    def disc(self, cx, cy, r, color, alpha=1.0):
        for y in range(int(cy - r), int(cy + r) + 1):
            for x in range(int(cx - r), int(cx + r) + 1):
                d2 = (x - cx) ** 2 + (y - cy) ** 2
                if d2 <= r * r:
                    # Soft 1px edge for cheap antialiasing.
                    d = d2 ** 0.5
                    a = alpha * min(1.0, max(0.0, r - d + 0.5))
                    self.blend(x, y, color, a)

    def line(self, x0, y0, x1, y1, width, color):
        r = max(width / 2, 0.5)
        length = ((x1 - x0) ** 2 + (y1 - y0) ** 2) ** 0.5
        steps = max(int(length / max(r * 0.5, 0.5)), 1)
        for s in range(steps + 1):
            t = s / steps
            self.disc(x0 + (x1 - x0) * t, y0 + (y1 - y0) * t, r, color)

    def write_png(self, path):
        raw = b"".join(
            b"\x00" + bytes(self.px[y * self.w * 3:(y + 1) * self.w * 3])
            for y in range(self.h)
        )

        def chunk(tag, data):
            c = tag + data
            return struct.pack(">I", len(data)) + c + struct.pack(">I", zlib.crc32(c))

        with open(path, "wb") as f:
            f.write(b"\x89PNG\r\n\x1a\n")
            f.write(chunk(b"IHDR", struct.pack(">IIBBBBB", self.w, self.h, 8, 2, 0, 0, 0)))
            f.write(chunk(b"IDAT", zlib.compress(raw, 6)))
            f.write(chunk(b"IEND", b""))


def attrs(tag):
    return dict(re.findall(r'([\w-]+)="([^"]*)"', tag))


def main():
    src = sys.argv[1]
    out = sys.argv[2] if len(sys.argv) > 2 else src.rsplit(".", 1)[0] + ".png"
    svg = open(src).read()

    w = int(re.search(r'width="(\d+)"', svg).group(1))
    h = int(re.search(r'height="(\d+)"', svg).group(1))
    canvas = Canvas(w, h)

    stops = [
        (float(m.group(1)), parse_color(m.group(2)))
        for m in re.finditer(r'<stop offset="([\d.]+)" stop-color="([^"]+)"', svg)
    ]

    n = 0
    for m in re.finditer(r"<(rect|line|circle)\b[^/]*/?>", svg):
        tag, a = m.group(1), attrs(m.group(0))
        if tag == "rect":
            if "url(#sky)" in a.get("fill", ""):
                canvas.gradient_rect(stops)
            else:
                canvas.fill_rect(float(a.get("x", 0)), float(a.get("y", 0)),
                                 float(a["width"]), float(a["height"]),
                                 parse_color(a["fill"]))
        elif tag == "line":
            canvas.line(float(a["x1"]), float(a["y1"]), float(a["x2"]), float(a["y2"]),
                        float(a.get("stroke-width", 1)), parse_color(a["stroke"]))
        elif tag == "circle":
            canvas.disc(float(a["cx"]), float(a["cy"]), float(a["r"]),
                        parse_color(a["fill"]), float(a.get("fill-opacity", 1)))
        n += 1

    canvas.write_png(out)
    print(f"rasterized {n} elements -> {out}")


if __name__ == "__main__":
    main()
