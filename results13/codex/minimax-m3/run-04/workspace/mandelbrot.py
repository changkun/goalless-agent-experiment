#!/usr/bin/env python3
"""Mandelbrot explorer — terminal ASCII + optional PNG/PBM export.

Keys (interactive mode):
  arrows / hjkl   pan
  + / -           zoom in / out
  r               reset view
  s               save image (PNG if Pillow available, else PBM/PPM)
  q               quit

Examples:
  python3 mandelbrot.py                # interactive, fits terminal
  python3 mandelbrot.py --width 160 --height 60 --max-iter 500
  python3 mandelbrot.py --render out.png --width 1280 --height 720 --max-iter 1000
"""
from __future__ import annotations

import argparse
import curses
import math
import os
import sys
import time
from dataclasses import dataclass


# A pleasant 16-colour gradient ramp (indices 0..15). Index 0 is "inside".
PALETTE = " .:-=+*#%@"
assert len(PALETTE) == 10


@dataclass
class View:
    cx: float = -0.5
    cy: float = 0.0
    span: float = 3.0   # width in the complex plane
    max_iter: int = 200

    def h(self):
        return self.span

    def w(self):
        return self.span


def render(view: View, width: int, height: int) -> list[str]:
    """Return a list of `height` strings of length `width`."""
    aspect = (width / max(1, height)) * 2.0  # chars are ~2x taller than wide
    span_w = view.span
    span_h = view.span / aspect
    out = []
    for y in range(height):
        row = []
        zy0 = view.cy - span_h / 2 + (y / max(1, height - 1)) * span_h
        for x in range(width):
            zx0 = view.cx - span_w / 2 + (x / max(1, width - 1)) * span_w
            zx = zy = 0.0
            it = 0
            zx2 = zy2 = 0.0
            while zx2 + zy2 <= 4.0 and it < view.max_iter:
                zy = 2.0 * zx * zy + zy0
                zx = zx2 - zy2 + zx0
                zx2 = zx * zx
                zy2 = zy * zy
                it += 1
            if it >= view.max_iter:
                row.append(PALETTE[0])
            else:
                # Smooth colouring via continuous escape value.
                log_zn = math.log(zx2 + zy2) / 2.0
                nu = math.log(log_zn / math.log(2.0)) / math.log(2.0)
                t = (it + 1 - nu) / view.max_iter
                idx = 1 + int(t * (len(PALETTE) - 1) * 0.999)
                idx = max(1, min(len(PALETTE) - 1, idx))
                row.append(PALETTE[idx])
        out.append("".join(row))
    return out


def render_to_pixels(view: View, width: int, height: int) -> bytes:
    """Render to 24-bit RGB PPM bytes (no external deps)."""
    span_w = view.span
    span_h = view.span * (height / max(1, width)) * 0.5  # square pixels
    max_iter = view.max_iter
    pixels = bytearray()
    for y in range(height):
        zy0 = view.cy - span_h / 2 + (y / max(1, height - 1)) * span_h
        for x in range(width):
            zx0 = view.cx - span_w / 2 + (x / max(1, width - 1)) * span_w
            zx = zy = 0.0
            zx2 = zy2 = 0.0
            it = 0
            while zx2 + zy2 <= 4.0 and it < max_iter:
                zy = 2.0 * zx * zy + zy0
                zx = zx2 - zy2 + zx0
                zx2 = zx * zx
                zy2 = zy * zy
                it += 1
            r, g, b = _colour(it, max_iter)
            pixels += bytes((r, g, b))
    header = f"P6\n{width} {height}\n255\n".encode()
    return header + bytes(pixels)


def _colour(it: int, max_iter: int) -> tuple[int, int, int]:
    if it >= max_iter:
        return (0, 0, 0)
    t = it / max_iter
    # Smooth cosine palette (Inigo Quilez style).
    a = (0.5, 0.5, 0.5)
    b = (0.5, 0.5, 0.5)
    c = (1.0, 1.0, 1.0)
    d = (0.0, 0.33, 0.67)
    r = int(255 * (a[0] + b[0] * math.cos(2 * math.pi * (c[0] * t + d[0]))))
    g = int(255 * (a[1] + b[1] * math.cos(2 * math.pi * (c[1] * t + d[1]))))
    b = int(255 * (a[2] + b[2] * math.cos(2 * math.pi * (c[2] * t + d[2]))))
    return max(0, min(255, r)), max(0, min(255, g)), max(0, min(255, b))


def save_image(path: str, view: View, width: int, height: int) -> None:
    ppm = render_to_pixels(view, width, height)
    base, ext = os.path.splitext(path)
    ext = ext.lower()
    try:
        from PIL import Image  # type: ignore
        import io
        img = Image.open(io.BytesIO(ppm))
        if ext in (".png", ".jpg", ".jpeg", ".bmp", ".tiff"):
            img.save(path)
        else:
            img.save(base + ".png")
            path = base + ".png"
        print(f"Wrote {path} ({width}x{height}, max_iter={view.max_iter})")
        return
    except Exception:
        pass
    # Fallback: write raw PPM.
    out = base + ".ppm"
    with open(out, "wb") as f:
        f.write(ppm)
    print(f"Wrote {out} ({width}x{height}, max_iter={view.max_iter}) — install Pillow for PNG")


def run_interactive(stdscr) -> None:
    curses.curs_set(0)
    stdscr.nodelay(True)
    view = View()
    last_save = 0.0
    status = "arrows/hjkl pan, +/- zoom, r reset, s save, q quit"
    while True:
        h, w = stdscr.getmaxyx()
        # Leave one line for status.
        grid_h = max(4, h - 1)
        grid_w = max(10, w)
        t0 = time.time()
        rows = render(view, grid_w, grid_h)
        dt = time.time() - t0
        stdscr.erase()
        for i, row in enumerate(rows):
            # clip to terminal width
            stdscr.addstr(i, 0, row[: w - 1])
        stdscr.addstr(h - 1, 0, f"{status}  |  span={view.span:.3g}  cx={view.cx:+.4f} cy={view.cy:+.4f}  iter={view.max_iter}  ({dt*1000:.0f}ms)")
        stdscr.refresh()

        key = stdscr.getch()
        if key == -1:
            time.sleep(0.05)
            continue
        step = view.span * 0.1
        if key in (curses.KEY_UP, ord("k")):
            view.cy -= step / 2
        elif key in (curses.KEY_DOWN, ord("j")):
            view.cy += step / 2
        elif key in (curses.KEY_LEFT, ord("h")):
            view.cx -= step
        elif key in (curses.KEY_RIGHT, ord("l")):
            view.cx += step
        elif key in (ord("+"), ord("=")):
            view.span *= 0.8
            view.max_iter = min(2000, view.max_iter + 25)
        elif key in (ord("-"), ord("_")):
            view.span *= 1.25
            view.max_iter = max(50, view.max_iter - 25)
        elif key == ord("r"):
            view = View()
        elif key == ord("s"):
            now = time.time()
            if now - last_save > 1.0:
                last_save = now
                try:
                    save_image("mandelbrot.png", view, 1280, 720)
                    status = "saved mandelbrot.png"
                except Exception as e:
                    status = f"save failed: {e}"
        elif key in (ord("q"), 27):
            return
        else:
            # small idle to avoid spinning at 100% on unknown keys
            time.sleep(0.02)


def main(argv: list[str]) -> int:
    p = argparse.ArgumentParser(description="Mandelbrot explorer (ASCII + image export)")
    p.add_argument("--width", type=int, default=0, help="image width (default: terminal width)")
    p.add_argument("--height", type=int, default=0, help="image height (default: terminal height)")
    p.add_argument("--max-iter", type=int, default=200, help="iteration limit")
    p.add_argument("--cx", type=float, default=-0.5, help="center x")
    p.add_argument("--cy", type=float, default=0.0, help="center y")
    p.add_argument("--span", type=float, default=3.0, help="view width in complex plane")
    p.add_argument("--render", type=str, default=None, help="render an image to this path and exit")
    p.add_argument("--no-interactive", action="store_true", help="do not launch the TUI")
    args = p.parse_args(argv)

    view = View(cx=args.cx, cy=args.cy, span=args.span, max_iter=args.max_iter)

    if args.render:
        w = args.width or 1280
        h = args.height or 720
        save_image(args.render, view, w, h)
        return 0

    if args.no_interactive or not sys.stdout.isatty():
        w = args.width or 80
        h = args.height or 40
        for row in render(view, w, h):
            print(row)
        return 0

    try:
        curses.wrapper(run_interactive)
    except KeyboardInterrupt:
        pass
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
