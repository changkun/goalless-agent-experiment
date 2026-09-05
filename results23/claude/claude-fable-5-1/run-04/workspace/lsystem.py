#!/usr/bin/env python3
"""L-system renderer with a hand-rolled PNG encoder. No dependencies.

Usage:
    python3 lsystem.py                # render all built-in systems to out/
    python3 lsystem.py dragon 14      # render one system at a given depth
"""
import math
import struct
import sys
import zlib

# ---------------------------------------------------------------- L-systems

SYSTEMS = {
    # name: (axiom, rules, turn angle in degrees, default depth)
    "dragon": ("FX", {"X": "X+YF+", "Y": "-FX-Y"}, 90, 13),
    "hilbert": ("A", {"A": "-BF+AFA+FB-", "B": "+AF-BFB-FA+"}, 90, 6),
    "koch": ("F--F--F", {"F": "F+F--F+F"}, 60, 5),
    "sierpinski": ("A", {"A": "B-A-B", "B": "A+B+A"}, 60, 8),
    "plant": ("X", {"X": "F+[[X]-X]-F[-FX]+X", "F": "FF"}, 25, 6),
    "levy": ("F", {"F": "+F--F+"}, 45, 14),
    "gosper": ("A", {"A": "A-B--B+A++AA+B-", "B": "+A-BB--B-A++A+B"}, 60, 4),
}


def expand(axiom, rules, depth):
    s = axiom
    for _ in range(depth):
        s = "".join(rules.get(c, c) for c in s)
    return s


def turtle(program, angle_deg, heading_deg=90.0):
    """Interpret an L-system string as turtle commands. Returns line segments.

    F/A/B/G draw forward; f moves without drawing; + and - turn; [ ] push/pop.
    Everything else is ignored (X, Y are pure rewriting symbols).
    """
    x = y = 0.0
    heading = math.radians(heading_deg)
    turn = math.radians(angle_deg)
    stack = []
    segs = []
    for c in program:
        if c in "FABG":
            nx, ny = x + math.cos(heading), y + math.sin(heading)
            segs.append((x, y, nx, ny))
            x, y = nx, ny
        elif c == "f":
            x, y = x + math.cos(heading), y + math.sin(heading)
        elif c == "+":
            heading += turn
        elif c == "-":
            heading -= turn
        elif c == "[":
            stack.append((x, y, heading))
        elif c == "]":
            x, y, heading = stack.pop()
    return segs


# ---------------------------------------------------------------- raster

class Canvas:
    def __init__(self, w, h, bg=(250, 247, 240)):
        self.w, self.h = w, h
        self.px = bytearray(bg * (w * h))

    def set(self, x, y, color, a=1.0):
        if 0 <= x < self.w and 0 <= y < self.h:
            i = 3 * (y * self.w + x)
            for k in range(3):
                self.px[i + k] = int(self.px[i + k] * (1 - a) + color[k] * a + 0.5)

    def line(self, x0, y0, x1, y1, color):
        """Xiaolin Wu anti-aliased line."""
        steep = abs(y1 - y0) > abs(x1 - x0)
        if steep:
            x0, y0, x1, y1 = y0, x0, y1, x1
        if x0 > x1:
            x0, x1, y0, y1 = x1, x0, y1, y0
        dx, dy = x1 - x0, y1 - y0
        grad = dy / dx if dx else 1.0
        y = y0
        for x in range(int(round(x0)), int(round(x1)) + 1):
            yi = int(math.floor(y))
            f = y - yi
            if steep:
                self.set(yi, x, color, 1 - f)
                self.set(yi + 1, x, color, f)
            else:
                self.set(x, yi, color, 1 - f)
                self.set(x, yi + 1, color, f)
            y += grad

    def downsample(self, factor):
        """Box filter by an integer factor. Returns a new Canvas."""
        out = Canvas(self.w // factor, self.h // factor)
        n = factor * factor
        for oy in range(out.h):
            for ox in range(out.w):
                acc = [0, 0, 0]
                for sy in range(factor):
                    row = 3 * ((oy * factor + sy) * self.w + ox * factor)
                    for sx in range(factor):
                        i = row + 3 * sx
                        acc[0] += self.px[i]
                        acc[1] += self.px[i + 1]
                        acc[2] += self.px[i + 2]
                j = 3 * (oy * out.w + ox)
                out.px[j] = acc[0] // n
                out.px[j + 1] = acc[1] // n
                out.px[j + 2] = acc[2] // n
        return out

    def write_png(self, path):
        def chunk(tag, data):
            body = tag + data
            return struct.pack(">I", len(data)) + body + struct.pack(">I", zlib.crc32(body) & 0xFFFFFFFF)

        raw = bytearray()
        stride = 3 * self.w
        for y in range(self.h):
            raw.append(0)  # filter type: none
            raw += self.px[y * stride:(y + 1) * stride]
        png = b"\x89PNG\r\n\x1a\n"
        png += chunk(b"IHDR", struct.pack(">IIBBBBB", self.w, self.h, 8, 2, 0, 0, 0))
        png += chunk(b"IDAT", zlib.compress(bytes(raw), 9))
        png += chunk(b"IEND", b"")
        with open(path, "wb") as f:
            f.write(png)


def lerp_color(a, b, t):
    return tuple(int(a[k] + (b[k] - a[k]) * t + 0.5) for k in range(3))


def render(name, depth=None, size=800, ss=3, path=None):
    axiom, rules, angle, default_depth = SYSTEMS[name]
    depth = default_depth if depth is None else depth
    segs = turtle(expand(axiom, rules, depth), angle)

    xs = [v for s in segs for v in (s[0], s[2])]
    ys = [v for s in segs for v in (s[1], s[3])]
    minx, maxx, miny, maxy = min(xs), max(xs), min(ys), max(ys)
    span = max(maxx - minx, maxy - miny) or 1.0
    margin = 0.06
    W = size * ss
    scale = W * (1 - 2 * margin) / span
    offx = (W - (maxx - minx) * scale) / 2
    offy = (W - (maxy - miny) * scale) / 2

    def tx(x): return (x - minx) * scale + offx
    def ty(y): return W - ((y - miny) * scale + offy)   # flip: y up

    big = Canvas(W, W)
    c0, c1 = (30, 60, 120), (200, 60, 40)   # colour along the path: start -> end
    n = len(segs)
    for i, (x0, y0, x1, y1) in enumerate(segs):
        big.line(tx(x0), ty(y0), tx(x1), ty(y1), lerp_color(c0, c1, i / max(n - 1, 1)))

    out = big.downsample(ss)
    path = path or f"out/{name}.png"
    out.write_png(path)
    return path, len(segs)


if __name__ == "__main__":
    if len(sys.argv) > 1:
        name = sys.argv[1]
        depth = int(sys.argv[2]) if len(sys.argv) > 2 else None
        p, n = render(name, depth)
        print(f"{name}: {n} segments -> {p}")
    else:
        for name in SYSTEMS:
            p, n = render(name)
            print(f"{name:12s} {n:>8d} segments -> {p}")
