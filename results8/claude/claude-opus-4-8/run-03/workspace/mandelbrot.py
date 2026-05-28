#!/usr/bin/env python3
"""
Truecolor Mandelbrot renderer for the terminal.

Renders the Mandelbrot set using half-block characters (each character cell
shows two vertical pixels via foreground/background colors), smooth-iteration
coloring, and a cyclic palette.

Examples:
    python3 mandelbrot.py                       # classic full view
    python3 mandelbrot.py --preset seahorse     # zoom into the Seahorse Valley
    python3 mandelbrot.py -cx -0.745 -cy 0.113 -z 250 -w 120

Press nothing — it just prints. Pipe through `less -R` to scroll.
"""
import argparse
import math
import shutil

# A few hand-picked scenic coordinates.
PRESETS = {
    "full":         (-0.5,      0.0,        1.3),
    "seahorse":     (-0.745,    0.1135,     90.0),
    "elephant":     ( 0.2925,   0.0149,    120.0),
    "spiral":       (-0.7453,   0.1127,    600.0),
    "minibrot":     (-1.74995,  0.0,       900.0),
    "tendrils":     (-0.235125, 0.827215,  400.0),
}


def smooth_iter(cx, cy, max_iter):
    """Return a smooth (fractional) escape count, or None if in the set."""
    zx = zy = 0.0
    for n in range(max_iter):
        zx2, zy2 = zx * zx, zy * zy
        if zx2 + zy2 > 256.0:
            # Smooth coloring: subtract log-log of the escape magnitude.
            mag = math.sqrt(zx2 + zy2)
            return n + 1 - math.log(math.log(mag)) / math.log(2)
        zy = 2.0 * zx * zy + cy
        zx = zx2 - zy2 + cx
    return None


def palette(t):
    """Map t in [0,1) to a smooth RGB color using cosine gradients."""
    a = 2.0 * math.pi
    r = int(127.5 * (1 + math.cos(a * (t + 0.00))))
    g = int(127.5 * (1 + math.cos(a * (t + 0.33))))
    b = int(127.5 * (1 + math.cos(a * (t + 0.67))))
    return r, g, b


def color_of(cx, cy, max_iter):
    it = smooth_iter(cx, cy, max_iter)
    if it is None:
        return (0, 0, 0)          # inside the set: black
    return palette(it * 0.025 % 1.0)


def render(cx, cy, zoom, width, height, max_iter):
    aspect = 0.5                  # half-blocks make each pixel ~square already
    span_x = 3.0 / zoom
    span_y = span_x * (height / width) / (1 / aspect)

    out = []
    # Two pixel-rows per text-row (top=fg, bottom=bg).
    for ty in range(0, height, 2):
        line = []
        for x in range(width):
            fx = cx + (x / width - 0.5) * span_x
            top_fy = cy + ((ty)     / height - 0.5) * span_y
            bot_fy = cy + ((ty + 1) / height - 0.5) * span_y
            tr, tg, tb = color_of(fx, top_fy, max_iter)
            br, bg, bb = color_of(fx, bot_fy, max_iter)
            line.append(f"\x1b[38;2;{tr};{tg};{tb}m"
                        f"\x1b[48;2;{br};{bg};{bb}m▀")
        line.append("\x1b[0m")
        out.append("".join(line))
    return "\n".join(out)


def main():
    cols, rows = shutil.get_terminal_size((100, 50))
    p = argparse.ArgumentParser(description="Terminal Mandelbrot renderer")
    p.add_argument("--preset", choices=PRESETS, help="scenic coordinate preset")
    p.add_argument("-cx", type=float, help="center real part")
    p.add_argument("-cy", type=float, help="center imaginary part")
    p.add_argument("-z", "--zoom", type=float, help="zoom factor")
    p.add_argument("-w", "--width", type=int, default=min(cols, 100))
    p.add_argument("-H", "--height", type=int, default=min(rows * 2, 60))
    p.add_argument("-i", "--iters", type=int, help="max iterations")
    args = p.parse_args()

    cx, cy, zoom = PRESETS[args.preset or "full"]
    if args.cx is not None: cx = args.cx
    if args.cy is not None: cy = args.cy
    if args.zoom is not None: zoom = args.zoom
    # Auto-scale iteration budget with zoom so deep views stay detailed.
    max_iter = args.iters or int(100 + 60 * math.log2(zoom + 1))

    print(render(cx, cy, zoom, args.width, args.height, max_iter))
    print(f"center=({cx}, {cy})  zoom={zoom}x  iters={max_iter}")


if __name__ == "__main__":
    main()
