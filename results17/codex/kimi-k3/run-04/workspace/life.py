#!/usr/bin/env python3
"""life.py -- a tiny terminal Game-of-Life toy, zero dependencies.

Three modes:
    python3 life.py            # live simulation in your terminal (Ctrl-C to stop)
    python3 life.py --export   # write life.html, an animated gallery of patterns
    python3 life.py --steps 5  # run 5 generations headlessly and print stats
"""

import argparse
import json
import os
import random
import sys
import time

NEWBORN_AGE = 1
# Older than this renders as an "ancient" cell.
ANCIENT_AGE = 12

# ---------------------------------------------------------------- patterns --

PATTERNS = {
    "glider": [
        ".O.",
        "..O",
        "OOO",
    ],
    "lightweight_spaceship": [
        ".O..O",
        "O....",
        "O...O",
        "OOOO.",
    ],
    "pulsar": [
        "..OOO...OOO..",
        ".............",
        "O....O.O....O",
        "O....O.O....O",
        "O....O.O....O",
        "..OOO...OOO..",
        ".............",
        "..OOO...OOO..",
        "O....O.O....O",
        "O....O.O....O",
        "O....O.O....O",
        ".............",
        "..OOO...OOO..",
    ],
    "pentadecathlon": [
        "..O....O..",
        "OO.OOOO.OO",
        "..O....O..",
    ],
    "acorn": [
        ".O.....",
        "...O...",
        "OO..OOO",
    ],
    "diehard": [
        "......O.",
        "OO......",
        ".O...OOO",
    ],
    "rpentomino": [
        ".OO",
        "OO.",
        ".O.",
    ],
    "gosper_glider_gun": [
        "........................O...........",
        "......................O.O...........",
        "............OO......OO............OO",
        "...........O...O....OO............OO",
        "OO........O.....O...OO..............",
        "OO........O...O.OO....O.O...........",
        "..........O.....O.......O...........",
        "...........O...O....................",
        "............OO......................",
    ],
}


def parse_pattern(rows):
    cells = set()
    for y, row in enumerate(rows):
        for x, ch in enumerate(row):
            if ch == "O":
                cells.add((x, y))
    return cells


def centered(pattern_name, width, height):
    rows = PATTERNS[pattern_name]
    cells = parse_pattern(rows)
    pw = max(len(r) for r in rows)
    ph = len(rows)
    ox = max(0, (width - pw) // 2)
    oy = max(0, (height - ph) // 2)
    return {(x + ox, y + oy) for (x, y) in cells}


# ------------------------------------------------------------------ engine --

def step(alive):
    """One generation over an unbounded plane.

    `alive` is a set of (x, y) tuples; returns (next_alive, births, deaths).
    """
    neighbor_counts = {}
    for (x, y) in alive:
        for dy in (-1, 0, 1):
            for dx in (-1, 0, 1):
                if dx == 0 and dy == 0:
                    continue
                key = (x + dx, y + dy)
                neighbor_counts[key] = neighbor_counts.get(key, 0) + 1

    next_alive = set()
    for cell, count in neighbor_counts.items():
        if count == 3 or (count == 2 and cell in alive):
            next_alive.add(cell)
    births = len(next_alive - alive)
    deaths = len(alive - next_alive)
    return next_alive, births, deaths


class World:
    """Bounded grid whose cells remember their age.

    Ages drive the color ramp in both the terminal and HTML renderers:
    newborn cells glow white, ancient ones settle into teal.
    """

    def __init__(self, width, height, seed_cells=(), wrap=False):
        self.width = width
        self.height = height
        self.wrap = wrap
        self.ages = {}
        for (x, y) in seed_cells:
            if 0 <= x < width and 0 <= y < height:
                self.ages[(x, y)] = NEWBORN_AGE
        self.generation = 0
        self.total_births = len(self.ages)
        self.total_deaths = 0

    def step(self):
        alive = set(self.ages)
        if self.wrap:
            alive = self._wrap_next(alive)
            births = len(alive - set(self.ages))
            deaths = len(set(self.ages) - alive)
        else:
            alive, births, deaths = step(alive)
            alive = {(x, y) for (x, y) in alive
                     if 0 <= x < self.width and 0 <= y < self.height}
        survivors = alive & set(self.ages)
        self.ages = {cell: self.ages[cell] + 1 for cell in survivors}
        for cell in alive - survivors:
            self.ages[cell] = NEWBORN_AGE
        self.total_births += births
        self.total_deaths += deaths
        self.generation += 1
        return births, deaths

    def _wrap_next(self, alive):
        neighbor_counts = {}
        for (x, y) in alive:
            for dy in (-1, 0, 1):
                for dx in (-1, 0, 1):
                    if dx == 0 and dy == 0:
                        continue
                    key = ((x + dx) % self.width, (y + dy) % self.height)
                    neighbor_counts[key] = neighbor_counts.get(key, 0) + 1
        return {c for c, n in neighbor_counts.items()
                if n == 3 or (n == 2 and c in alive)}


# ------------------------------------------------------- terminal renderer --

BRIGHT_WHITE = "\x1b[97m"
YELLOW = "\x1b[93m"
ORANGE = "\x1b[33m"
MAGENTA = "\x1b[35m"
BLUE = "\x1b[34m"
CYAN = "\x1b[36m"
RESET = "\x1b[0m"
GLYPH = "██"


def age_color(age):
    if age <= 1:
        return BRIGHT_WHITE
    if age <= 2:
        return YELLOW
    if age <= 4:
        return ORANGE
    if age <= 7:
        return MAGENTA
    if age <= ANCIENT_AGE:
        return BLUE
    return CYAN


def render_terminal(world):
    lines = []
    for y in range(world.height):
        row = []
        for x in range(world.width):
            age = world.ages.get((x, y))
            row.append(age_color(age) + GLYPH + RESET if age else "  ")
        lines.append("".join(row))
    stats = (f" gen {world.generation}  pop {len(world.ages)}"
             f"  +{world.total_births} born  -{world.total_deaths} died")
    return "\n".join(lines) + "\n" + CYAN + stats + RESET


def run_live(pattern=None, density=0.16, fps=12):
    if sys.stdout.isatty():
        term = os.get_terminal_size()
    else:
        term = os.terminal_size((100, 30))
    width = max(10, term.columns // 2 - 2)
    height = max(10, term.lines - 4)

    if pattern:
        seeds = centered(pattern, width, height)
        title = pattern.replace("_", " ")
    else:
        rng = random.Random()
        cx, cy, r = width // 2, height // 2, min(width, height) // 2
        seeds = {(x, y)
                 for x in range(cx - r, cx + r)
                 for y in range(cy - r, cy + r)
                 if rng.random() < density}
        title = f"random soup ({density:.0%} density)"

    world = World(width, height, seeds)
    sys.stdout.write("\x1b[?25l")  # hide cursor
    try:
        print(f"\x1b[1mlife.py\x1b[0m -- {title} -- Ctrl-C to stop")
        while True:
            sys.stdout.write("\x1b[H\n")
            sys.stdout.write(render_terminal(world) + "\n")
            sys.stdout.flush()
            if not world.ages:
                print("all dead. the void wins.")
                break
            world.step()
            time.sleep(1 / fps)
    except KeyboardInterrupt:
        pass
    finally:
        sys.stdout.write("\x1b[?25h\n")  # restore cursor


# ------------------------------------------------------------ HTML export --

def age_color_css(age):
    if age <= 1:
        return "#ffffff"
    if age <= 2:
        return "#ffd166"
    if age <= 4:
        return "#f4a261"
    if age <= 7:
        return "#e056a0"
    if age <= ANCIENT_AGE:
        return "#5b6cff"
    return "#43e0c8"


def simulate_frames(pattern_name, width, height, frames):
    world = World(width, height, centered(pattern_name, width, height))
    out = []
    for _ in range(frames):
        out.append({f"{x},{y}": age for (x, y), age in world.ages.items()})
        world.step()
    return out


HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>life.py -- pattern gallery</title>
<style>
  :root {{ --bg: #0b0e1a; --panel: #141a2e; --text: #cdd6f4; --dim: #6c7699; }}
  * {{ box-sizing: border-box; }}
  body {{ margin: 0; background: var(--bg); color: var(--text);
         font: 15px/1.5 ui-monospace, Menlo, Consolas, monospace; }}
  header {{ padding: 2rem 1rem 0.5rem; text-align: center; }}
  h1 {{ margin: 0; font-size: 1.6rem; letter-spacing: 0.12em; }}
  header p {{ color: var(--dim); margin: 0.4rem auto 0; max-width: 46rem; }}
  main {{ display: grid; gap: 1rem; padding: 1.5rem; max-width: 1100px;
         margin: 0 auto; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); }}
  figure {{ margin: 0; background: var(--panel); border-radius: 12px;
           padding: 1rem; display: flex; flex-direction: column; gap: 0.6rem; }}
  figcaption {{ display: flex; justify-content: space-between; color: var(--dim); }}
  figcaption b {{ color: var(--text); font-weight: 600; }}
  canvas {{ width: 100%; image-rendering: pixelated; border-radius: 6px;
           background: #0e1220; }}
  footer {{ text-align: center; color: var(--dim); padding: 1rem 1rem 2.5rem; }}
</style>
</head>
<body>
<header>
  <h1>life.py</h1>
  <p>Conway&rsquo;s Game of Life &mdash; {count} patterns, {frames} generations each.
     Cells age: white &rarr; gold &rarr; orange &rarr; pink &rarr; indigo &rarr; teal.</p>
</header>
<main id="gallery"></main>
<footer>generated by life.py &mdash; pure python, zero dependencies</footer>
<script>
const GALLERY = {data};
const CELL = 8, GAP = 1, FRAME_MS = 110;

for (const item of GALLERY) {{
  const fig = document.createElement("figure");
  const cap = document.createElement("figcaption");
  const name = document.createElement("b");
  name.textContent = item.name.replaceAll("_", " ");
  const meta = document.createElement("span");
  const canvas = document.createElement("canvas");
  canvas.width = item.width * (CELL + GAP);
  canvas.height = item.height * (CELL + GAP);
  cap.append(name, meta);
  fig.append(cap, canvas);
  document.getElementById("gallery").append(fig);

  const ctx = canvas.getContext("2d");
  const palette = {{}};
  for (const [limit, hex] of item.palette) palette[limit] = hex;
  const limits = Object.keys(palette).map(Number).sort((a, b) => a - b);
  const colorFor = age => {{
    for (const limit of limits) if (age <= limit) return palette[limit];
    return palette[limits[limits.length - 1]];
  }};

  let f = 0;
  setInterval(() => {{
    const frame = item.frames[f];
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    for (const [key, age] of Object.entries(frame)) {{
      const [x, y] = key.split(",").map(Number);
      ctx.fillStyle = colorFor(age);
      ctx.fillRect(x * (CELL + GAP), y * (CELL + GAP), CELL, CELL);
    }}
    meta.textContent = "gen " + f;
    f = (f + 1) % item.frames.length;
  }}, FRAME_MS);
}}
</script>
</body>
</html>
"""


def export_html(path="life.html", frames=90):
    gallery = []
    for name, rows in PATTERNS.items():
        pw = max(len(r) for r in rows)
        ph = len(rows)
        width = max(pw + 8, 44)
        height = max(ph + 8, 26)
        palette = [[age, age_color_css(age)]
                   for age in (1, 2, 4, 7, ANCIENT_AGE, 10 ** 9)]
        gallery.append({
            "name": name,
            "width": width,
            "height": height,
            "palette": palette,
            "frames": simulate_frames(name, width, height, frames),
        })
    data = json.dumps(gallery, separators=(",", ":"))
    page = HTML_TEMPLATE.format(count=len(gallery), frames=frames, data=data)
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(page)
    return path


# --------------------------------------------------------------------- CLI --

def headless(steps, pattern="acorn"):
    world = World(70, 40, centered(pattern, 70, 40))
    for _ in range(steps):
        world.step()
    print(f"pattern    : {pattern}")
    print(f"generations: {world.generation}")
    print(f"population : {len(world.ages)}")
    print(f"births     : {world.total_births}")
    print(f"deaths     : {world.total_deaths}")


def main(argv=None):
    parser = argparse.ArgumentParser(description="tiny terminal Game of Life")
    parser.add_argument("--pattern", choices=sorted(PATTERNS),
                        help="seed with a named pattern instead of random soup")
    parser.add_argument("--export", action="store_true",
                        help="write life.html, an animated pattern gallery")
    parser.add_argument("--steps", type=int, metavar="N",
                        help="run N generations headlessly and print stats")
    parser.add_argument("--fps", type=int, default=12)
    args = parser.parse_args(argv)

    if args.export:
        path = export_html()
        print(f"wrote {path} -- open it in a browser")
    elif args.steps is not None:
        headless(args.steps, args.pattern or "acorn")
    else:
        run_live(pattern=args.pattern, fps=args.fps)


if __name__ == "__main__":
    main()
