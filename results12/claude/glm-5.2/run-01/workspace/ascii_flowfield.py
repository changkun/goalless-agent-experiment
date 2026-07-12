#!/usr/bin/env python3
"""
ascii_flowfield.py — A procedural terminal "flow field" renderer.

Particles wander across a vector field defined by a sum of sine waves.
Their paths are stamped into a character buffer; brighter cells use
denser ASCII glyphs. Press Ctrl-C to stop; runs for a fixed number of
frames unless --loop is given.
"""
import argparse
import math
import os
import random
import shutil
import sys
import time

# Glyph ramp from sparse to dense.
RAMP = " .,-~:;=!*#$@"
RAMP_LEN = len(RAMP)


class Field:
    """A 2D scalar accumulation buffer mapped onto an ASCII ramp."""

    def __init__(self, width, height, decay=0.92, cap=6.0):
        self.w = width
        self.h = height
        self.decay = decay
        self.cap = cap
        self.buf = [0.0] * (width * height)

    def stamp(self, x, y, amount=1.0):
        ix, iy = int(x), int(y)
        if 0 <= ix < self.w and 0 <= iy < self.h:
            i = iy * self.w + ix
            self.buf[i] = min(self.cap, self.buf[i] + amount)

    def age(self):
        d = self.decay
        b = self.buf
        for i in range(len(b)):
            b[i] *= d

    def render(self):
        ramp = RAMP
        rl = RAMP_LEN
        cap = self.cap
        out = []
        b = self.buf
        for y in range(self.h):
            base = y * self.w
            row = []
            for x in range(self.w):
                v = b[base + x]
                if v < 0.02:
                    row.append(" ")
                else:
                    idx = int(v / cap * (rl - 1))
                    if idx < 0:
                        idx = 0
                    elif idx >= rl:
                        idx = rl - 1
                    row.append(ramp[idx])
            out.append("".join(row))
        return "\n".join(out)


def field_angle(x, y, t, seed):
    """Angle of the flow vector at (x,y) at time t."""
    # Layered sine waves create organic, slowly-evolving curls.
    s = seed
    a = (math.sin(x * 0.13 + t * 0.30 + s)
         + math.cos(y * 0.11 - t * 0.21 + s * 1.7)
         + math.sin((x + y) * 0.07 + t * 0.13 + s * 0.5)) / 3.0
    return a * math.pi


def main():
    ap = argparse.ArgumentParser(description="ASCII flow field renderer.")
    ap.add_argument("--frames", type=int, default=200,
                    help="number of frames to render (0 = use --loop)")
    ap.add_argument("--particles", type=int, default=120,
                    help="number of wandering particles")
    ap.add_argument("--steps", type=int, default=8,
                    help="movement substeps per particle per frame")
    ap.add_argument("--seed", type=int, default=None,
                    help="random seed for reproducibility")
    ap.add_argument("--loop", action="store_true",
                    help="run until Ctrl-C")
    ap.add_argument("--fps", type=float, default=30.0,
                    help="target frames per second")
    args = ap.parse_args()

    if args.seed is not None:
        random.seed(args.seed)
    seed = random.random() * 100.0

    cols, rows = shutil.get_terminal_size((80, 24))
    # Leave one row so we don't scroll on every frame.
    w, h = max(10, cols), max(6, rows - 1)

    field = Field(w, h, decay=0.93, cap=5.0)
    particles = [
        {
            "x": random.uniform(0, w),
            "y": random.uniform(0, h),
            "life": random.randint(20, 80),
        }
        for _ in range(args.particles)
    ]

    # Hide cursor + clear screen.
    sys.stdout.write("\x1b[?25l\x1b[2J")
    sys.stdout.flush()

    def cleanup():
        sys.stdout.write("\x1b[?25h\x1b[2J\x1b[H")
        sys.stdout.flush()

    frame = 0
    target_dt = 1.0 / args.fps if args.fps > 0 else 0
    try:
        running = True
        while running:
            start = time.monotonic()
            t = frame * 0.05
            step = 0.9  # cell units per substep

            for p in particles:
                if p["life"] <= 0:
                    p["x"] = random.uniform(0, w)
                    p["y"] = random.uniform(0, h)
                    p["life"] = random.randint(20, 80)
                ang = field_angle(p["x"], p["y"], t, seed)
                dx = math.cos(ang) * step
                dy = math.sin(ang) * step * 0.5  # squashed — chars are tall
                nx, ny = p["x"] + dx, p["y"] + dy
                # Soft bounce off the edges.
                if nx < 0 or nx >= w:
                    nx = max(0.0, min(w - 0.001, nx))
                if ny < 0 or ny >= h:
                    ny = max(0.0, min(h - 0.001, ny))
                field.stamp(p["x"], p["y"], 0.8)
                p["x"], p["y"] = nx, ny
                p["life"] -= 1
                for _ in range(args.steps - 1):
                    if p["life"] <= 0:
                        break
                    ang = field_angle(p["x"], p["y"], t, seed)
                    dx = math.cos(ang) * step
                    dy = math.sin(ang) * step * 0.5
                    p["x"] = max(0.0, min(w - 0.001, p["x"] + dx))
                    p["y"] = max(0.0, min(h - 0.001, p["y"] + dy))
                    field.stamp(p["x"], p["y"], 0.8)
                    p["life"] -= 1

            field.age()

            # Move to top-left and redraw.
            sys.stdout.write("\x1b[H")
            sys.stdout.write(field.render())
            sys.stdout.flush()

            frame += 1
            if not args.loop and args.frames > 0 and frame >= args.frames:
                running = False

            if target_dt > 0:
                elapsed = time.monotonic() - start
                remaining = target_dt - elapsed
                if remaining > 0:
                    time.sleep(remaining)
    except KeyboardInterrupt:
        pass
    finally:
        cleanup()


if __name__ == "__main__":
    main()
