"""
Mandelbrot set renderer — ASCII art with color gradients via ANSI escape codes.
Renders the classic fractal in your terminal using iteration-depth coloring.
"""

import sys
import os

# ANSI 256-color escape
def color(n):
    return f"\x1b[38;5;{n}m"

RESET = "\x1b[0m"

# A palette cycling through blues → cyans → magentas → golds → white
PALETTE = (
    [17, 18, 19, 20, 21]          # dark blues
    + [27, 33, 39, 45, 51]        # blues → cyan
    + [50, 49, 48, 47, 46]        # cyan → green
    + [82, 118, 154, 190, 226]    # green → yellow
    + [220, 214, 208, 202, 196]   # yellow → red
    + [197, 198, 199, 200, 201]   # red → magenta
    + [165, 129, 93, 57, 21]      # magenta → blue
    + [255, 254, 253, 252, 251]   # near-white
)

def mandelbrot(cx, cy, max_iter=256):
    x, y = 0.0, 0.0
    for i in range(max_iter):
        if x*x + y*y > 4.0:
            return i
        x, y = x*x - y*y + cx, 2*x*y + cy
    return max_iter

def render(
    width=120, height=40,
    x_min=-2.5, x_max=1.0,
    y_min=-1.1, y_max=1.1,
    max_iter=256,
    use_color=True,
):
    chars = " .:+*=%@#$"
    rows = []
    for row in range(height):
        cy = y_min + (y_max - y_min) * row / (height - 1)
        line = []
        for col in range(width):
            cx = x_min + (x_max - x_min) * col / (width - 1)
            n = mandelbrot(cx, cy, max_iter)
            if n == max_iter:
                ch = " "
                c = ""
            else:
                ch = chars[n % len(chars)]
                if use_color:
                    c = color(PALETTE[n % len(PALETTE)])
                else:
                    c = ""
            if use_color:
                line.append(f"{c}{ch}{RESET if c else ''}")
            else:
                line.append(ch)
        rows.append("".join(line))
    return "\n".join(rows)

def main():
    no_color = "--no-color" in sys.argv or not sys.stdout.isatty()

    # Detect terminal size
    try:
        cols, lines = os.get_terminal_size()
        w = min(cols, 140)
        h = min(lines - 4, 50)
    except OSError:
        w, h = 120, 40

    print(f"\nMandelbrot Set  ({w}×{h})\n")
    print(render(width=w, height=h, use_color=not no_color))
    print()

    # Print a miniature zoom into the Seahorse Valley
    zoom_w, zoom_h = min(w, 80), min(h, 24)
    print(f"Seahorse Valley zoom  ({zoom_w}×{zoom_h})\n")
    print(render(
        width=zoom_w, height=zoom_h,
        x_min=-0.76, x_max=-0.72,
        y_min=0.08,  y_max=0.12,
        max_iter=512,
        use_color=not no_color,
    ))
    print()

if __name__ == "__main__":
    main()
