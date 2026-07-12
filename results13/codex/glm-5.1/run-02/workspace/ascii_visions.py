#!/usr/bin/env python3
"""
✦ ASCII Visions ✦
A generative ASCII art program that creates procedural patterns.
Run: python3 ascii_visions.py
"""

import random
import math
import time
import sys
import os

CHARSETS = {
    "ethereal": "·˙:∘○◎●◌○◌˙·:∘◎●✦✧⋆✶✷✸✹✺✻✼❋",
    "cosmic":  " .:-=+*#%@░▒▓█▄▀▌▐⌐¬∝∞≡⌁⌯",
    "organic": " ⢎⢑⢔⢕⢖⢗⢘⢙⢚⢛⢜⢝⢞⢟⡠⡡⡢⡣⡤⡥",
    "waves":   " ~≈∿≋⌇⋏⋎⋔⋞⋟⋏⋎≋∿≈~",
    "minimal": " ·:+*#",
}

def plasma_field(width, height, t):
    """Generate a plasma-like value field."""
    field = []
    for y in range(height):
        row = []
        for x in range(width):
            v = 0
            v += math.sin(x * 0.05 + t)
            v += math.sin(y * 0.07 + t * 0.7)
            v += math.sin((x + y) * 0.03 + t * 0.5)
            cx, cy = width / 2, height / 2
            v += math.sin(math.sqrt((x - cx)**2 + (y - cy)**2) * 0.06 + t * 1.3)
            v = (v + 4) / 8  # normalize to ~0..1
            row.append(v)
        field.append(row)
    return field

def spiral_field(width, height, t):
    """Generate a spiral pattern."""
    field = []
    cx, cy = width / 2, height / 2
    for y in range(height):
        row = []
        for x in range(width):
            dx, dy = x - cx, y - cy
            dist = math.sqrt(dx*dx + dy*dy)
            angle = math.atan2(dy, dx)
            v = (math.sin(angle * 3 + dist * 0.15 - t * 2) + 1) / 2
            fade = max(0, 1 - dist / (min(width, height) * 0.5))
            v *= fade
            row.append(v)
        field.append(row)
    return field

def interference_field(width, height, t):
    """Generate wave interference pattern."""
    field = []
    sources = [(width * 0.25, height * 0.3), (width * 0.75, height * 0.6), (width * 0.5, height * 0.8)]
    for y in range(height):
        row = []
        for x in range(width):
            v = 0
            for sx, sy in sources:
                dist = math.sqrt((x - sx)**2 + (y - sy)**2)
                v += math.sin(dist * 0.2 - t * 2)
            v = (v / len(sources) + 1) / 2
            row.append(v)
        field.append(row)
    return field

def mandala_field(width, height, t):
    """Generate a mandala-like radial pattern."""
    field = []
    cx, cy = width / 2, height / 2
    for y in range(height):
        row = []
        for x in range(width):
            dx, dy = x - cx, y - cy
            dist = math.sqrt(dx*dx + dy*dy)
            angle = math.atan2(dy, dx)
            petals = 6
            v = (math.sin(angle * petals + dist * 0.1 + t) + 
                 math.sin(angle * petals * 2 - dist * 0.15 + t * 1.5) +
                 math.cos(dist * 0.2 - t * 0.8))
            v = (v + 3) / 6
            ring = math.sin(dist * 0.25 + t * 0.3) * 0.3 + 0.7
            v *= ring
            row.append(max(0, min(1, v)))
        field.append(row)
    return field

def flow_field(width, height, t):
    """Generate a flowing noise-like pattern using sin compositions."""
    field = []
    for y in range(height):
        row = []
        for x in range(width):
            nx, ny = x / width, y / height
            v = 0
            v += math.sin(nx * 10 + t) * math.cos(ny * 8 + t * 0.6)
            v += math.sin(nx * 5 - ny * 7 + t * 0.8) * 0.5
            v += math.cos(nx * 12 + ny * 4 + t * 1.2) * 0.3
            v = (v + 1.8) / 3.6
            row.append(max(0, min(1, v)))
        field.append(row)
    return field

PATTERNS = {
    "plasma":     plasma_field,
    "spiral":     spiral_field,
    "interference": interference_field,
    "mandala":    mandala_field,
    "flow":       flow_field,
}

def render_field(field, charset_name, width, height, invert=False):
    """Render a value field to ASCII art."""
    chars = CHARSETS.get(charset_name, CHARSETS["minimal"])
    lines = []
    for y in range(height):
        line = ""
        for x in range(width):
            v = field[y][x]
            if invert:
                v = 1 - v
            idx = int(v * (len(chars) - 1))
            idx = max(0, min(len(chars) - 1, idx))
            # Aspect ratio correction: double up horizontally
            line += chars[idx] * 2
        lines.append(line)
    return "\n".join(lines)

def colorize(text, palette="auto"):
    """Add ANSI color to the output."""
    colors = [
        "\033[38;5;69m",   # blue
        "\033[38;5;99m",   # purple
        "\033[38;5;213m",  # pink
        "\033[38;5;51m",   # cyan
        "\033[38;5;84m",   # green
        "\033[38;5;228m",  # gold
        "\033[38;5;222m",  # peach
        "\033[38;5;180m",  # amber
    ]
    reset = "\033[0m"
    result = []
    for i, line in enumerate(text.split("\n")):
        c = colors[i % len(colors)]
        result.append(f"{c}{line}{reset}")
    return "\n".join(result)

def animate(pattern_name, charset_name, width, height, color=True, invert=False, frames=200, fps=10):
    """Animate the pattern."""
    generator = PATTERNS.get(pattern_name, plasma_field)
    interval = 1.0 / fps
    
    clear = "\033[2J\033[H"
    hide_cursor = "\033[?25l"
    show_cursor = "\033[?25h"
    
    sys.stdout.write(hide_cursor)
    
    try:
        for frame in range(frames):
            t = frame * 0.08
            field = generator(width, height, t)
            text = render_field(field, charset_name, width, height, invert)
            if color:
                text = colorize(text)
            sys.stdout.write(clear)
            sys.stdout.write(f"  ✦ {pattern_name.title()} Vision — frame {frame+1}/{frames} ✦\n\n")
            sys.stdout.write(text)
            sys.stdout.write(f"\n\n  [q]uit  [r]andom  pattern:{pattern_name}  charset:{charset_name}")
            sys.stdout.flush()
            time.sleep(interval)
    except KeyboardInterrupt:
        pass
    finally:
        sys.stdout.write(show_cursor + "\n")
        sys.stdout.flush()

def show_static(pattern_name, charset_name, width, height, color=True, invert=False):
    """Show a single frame."""
    generator = PATTERNS.get(pattern_name, plasma_field)
    field = generator(width, height, random.uniform(0, 10))
    text = render_field(field, charset_name, width, height, invert)
    if color and sys.stdout.isatty():
        text = colorize(text)
    print(f"  ✦ {pattern_name.title()} Vision ✦\n")
    print(text)
    print()

def main():
    cols, rows = 40, 18
    if sys.stdout.isatty():
        try:
            size = os.get_terminal_size()
            cols = max(20, (size.columns - 4) // 2)
            rows = max(8, size.lines - 6)
        except:
            pass

    args = sys.argv[1:]
    
    pattern = random.choice(list(PATTERNS.keys()))
    charset = random.choice(list(CHARSETS.keys()))
    animate_flag = "-a" in args or "--animate" in args
    color_flag = not ("--no-color" in args or "-n" in args)
    invert_flag = "--invert" in args or "-i" in args
    static_flag = "--static" in args or "-s" in args
    
    for a in args:
        if a in PATTERNS:
            pattern = a
        if a in CHARSETS:
            charset = a

    if animate_flag and sys.stdout.isatty():
        animate(pattern, charset, cols, rows, color_flag, invert_flag)
    else:
        show_static(pattern, charset, cols, rows, color_flag, invert_flag)

if __name__ == "__main__":
    main()
