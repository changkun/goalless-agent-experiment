#!/usr/bin/env python3
"""Conway's Game of Life and other cellular automata, in pure Python.

Zero dependencies. Runs in the terminal.

Usage:
    python3 life.py                     # random soup under classic Life
    python3 life.py <pattern> [<rule>]  # e.g. python3 life.py glider
    python3 life.py list                # show available patterns and rules
    python3 life.py html                # write an animated life.html you can open

Examples:
    python3 life.py glider life
    python3 life.py r-pentomino life
    python3 life.py pulsar highlife
    python3 life.py soup seeds
"""

import argparse
import random
import sys
import time

W, H = 78, 30          # grid dimensions (terminal-friendly)
GENERATIONS = 120      # default ticks
FRAME = 0.06           # seconds between frames in terminal mode

# ---------------------------------------------------------------------------
# Rule universe: (B, S) sets from Wikipedia's "Life-like cellular automaton".
# B = count of live neighbours that makes a dead cell come alive.
# S = count of live neighbours that keeps a live cell alive.
# ---------------------------------------------------------------------------
RULES = {
    "life":     ({3},        {2, 3}),      # Conway's Game of Life
    "highlife": ({3, 6},     {2, 3}),      # Life + the "6" cell
    "seeds":    ({2},        set()),       # every cell dies each tick
    "daynight": ({3, 4, 6, 7, 8}, {3, 4, 5, 6, 7, 8}),
    "maze":     ({3},        {1, 2, 3, 4, 5}),  # grows mazelike corridors
    "pulsar":   ({3},        {2, 3, 4}),   # a moving "pulsar" variant
    "fredkin":  (set(r for r in range(9) if r % 2 == 1),
                 {r for r in (0, 1, 2, 3, 4, 5, 6, 7, 8) if r % 2 == 0}),
}

# ---------------------------------------------------------------------------
# Patterns centred on the grid.  '.' dead, 'o' alive.
# ---------------------------------------------------------------------------
PATTERNS = {
    "glider": [
        ".o.",
        "..o",
        "ooo",
    ],
    "r-pentomino": [
        ".oo",
        "oo.",
        ".o.",
    ],
    "pulsar": [   # a small still-ish oscillator (the period-3 period)
        "..ooo...ooo..",
        "...........",
        "o....o.o....o",
        "o....o.o....o",
        "o....o.o....o",
        "..ooo...ooo..",
        "...........",
        "..ooo...ooo..",
        "o....o.o....o",
        "o....o.o....o",
        "o....o.o....o",
        "...........",
        "..ooo...ooo..",
    ],
    "gosper": [   # a readable slice of the Gosper glider gun
        ".........................o............",
        ".......................o.o............",
        ".............o......oo............oo..",
        "............o.o......oo............oo.",
        "..oo........oo........................",
        "..oo.......o.o........................",
        "...........o..........................",
        "..............................o.......",
        ".............................o.o......",
        "..............oo.............oo.......",
        "..............oo......oo...oo.........",
        "........................oo...oo........",
    ],
}

HELP_LINES = [
    "Legend:  o = alive    . = empty",
    "",
    "Available patterns: " + ", ".join(sorted(PATTERNS)),
    "",
    "Available rules:    " + ", ".join(sorted(RULES)),
]


def make_grid(pattern_name):
    """Return a HxW grid (list of list of ints) seeded with the pattern."""
    grid = [[0] * W for _ in range(H)]
    cell = PATTERNS.get(pattern_name)
    if cell is None:
        raise SystemExit(f"unknown pattern {pattern_name!r}")
    ph, pw = len(cell), len(cell[0])
    x0, y0 = (W - pw) // 2, (H - ph) // 2
    for y, row in enumerate(cell):
        for x, ch in enumerate(row):
            if ch == "o":
                grid[y0 + y][x0 + x] = 1
    return grid


def random_grid(seed=0):
    """Random soup with roughly 30% of cells alive."""
    rng = random.Random(seed)
    return [[1 if rng.random() < 0.30 else 0 for _ in range(W)]
            for _ in range(H)]


def step(grid, birth, survive):
    """Advance one generation.  Pure Python, no imports beyond stdlib."""
    # Derive dimensions from the grid itself so `step` works on any size.
    H_ = len(grid)
    W_ = len(grid[0]) if H_ else 0
    new = [row[:] for row in grid]
    for y in range(H_):
        row = grid[y]
        newrow = new[y]
        for x in range(W_):
            n = 0
            for dy in (-1, 0, 1):
                ny = y + dy
                if not 0 <= ny < H_:
                    continue
                other = grid[ny]
                for dx in (-1, 0, 1):
                    if dx == 0 and dy == 0:
                        continue
                    nx = x + dx
                    if 0 <= nx < W_ and other[nx]:
                        n += 1
            if row[x]:
                newrow[x] = 1 if n in survive else 0
            else:
                newrow[x] = 1 if n in birth else 0
    return new


def render(grid):
    return "\n".join("".join("o" if c else "." for c in row) for row in grid)


def live_count(grid):
    return sum(sum(row) for row in grid)


def run(pattern, rule, gens, out_html=False, out_path="life.html",
        seed=None):
    birth, survive = RULES[rule]
    grid = make_grid(pattern) if pattern else random_grid(seed)
    frames = []

    for g in range(gens):
        frames.append((g, render(grid), live_count(grid)))
        grid = step(grid, birth, survive)

    if out_html:
        write_html(frames, rule, pattern, out_path)
        print(f"wrote {out_path}  ({len(frames)} frames)")
        return

    # Terminal mode: clear screen between frames for a smooth-ish animation.
    for g, text, count in frames:
        sys.stdout.write("\033[H\033[2J")          # home + clear
        sys.stdout.write(
            f"{rule:>8} . {pattern or 'soup'} . gen {g:>3} . alive {count}\n\n")
        sys.stdout.write(text)
        sys.stdout.flush()
        time.sleep(FRAME)
    print()


def write_html(frames, rule, pattern, path):
    """Emit a tiny self-contained animated page (no JS libraries).

    The script is a plain (non-f) string with __TOKEN__ markers, replaced
    below, so the JavaScript's own braces never collide with Python's
    formatting syntax.
    """
    import json
    title = f"{rule} — {pattern or 'soup'} — Game of Life"
    frames_src = json.dumps([f[1] for f in frames])
    alive_src = json.dumps([f[2] for f in frames])
    status = f"{rule} &middot; {pattern or 'soup'} &middot; gen "    # open to appends

    page = """<!doctype html><html><head><meta charset="utf-8">
<title>__TITLE__</title>
<style>
  body{background:#0d1117;color:#e6edf3;font:16px/1.15 ui-monospace,monospace;
       display:flex;flex-direction:column;align-items:center;padding:24px;}
  #status{margin-bottom:12px;color:#7d8590;}
  canvas{background:#010409;border:1px solid #30363d;border-radius:6px;}
</style></head><body>
<div id="status"></div>
<canvas id="c" width="__CW__" height="__CH__"></canvas>
<script>
const frames = __FRAMES__;
const alive = __ALIVE__;
const canvas = document.getElementById('c');
const ctx = canvas.getContext('2d');
const cell = 7, gap = 1, off = 3;
const st = document.getElementById('status');
let i = 0, running = true;
const DELAY = 90;
function draw(){
  ctx.clearRect(0,0,canvas.width,canvas.height);
  const rows = frames[i].split("\\n");
  for(let y=0;y<rows.length;y++)for(let x=0;x<rows[y].length;x++){
    if(rows[y][x]==='o'){
      ctx.fillStyle='#3fb950';
      ctx.fillRect(off+x*(cell+gap), off+y*(cell+gap), cell, cell);
    }
  }
  st.textContent = '__STATUS__' + i + ' · alive ' + alive[i];
}
setInterval(()=>{ if(running){ draw(); i=(i+1)%frames.length; } }, DELAY);
canvas.onclick = ()=>{ running=!running; draw(); };
draw();
</script></body></html>"""
    page = (page
            .replace("__TITLE__", title)
            .replace("__CW__", str(W * 7))
            .replace("__CH__", str(H * 12))
            .replace("__FRAMES__", frames_src)
            .replace("__ALIVE__", alive_src)
            .replace("__STATUS__", status))
    with open(path, "w") as f:
        f.write(page)


# The --no-serialization of pre/EINLINE: build the compact JSON payloads here
# so the template above stays readable.  (Frames are just strings.)
def frames_json(frames):
    import json
    return json.dumps([f[1] for f in frames])

def frames_alive(frames):
    import json
    return json.dumps([f[2] for f in frames])


def main(argv=None):
    p = argparse.ArgumentParser(
        description="Life-like cellular automata, pure Python.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="\n".join(HELP_LINES))
    p.add_argument("pattern", nargs="?", default=None,
                   help="named pattern, or omit for a random soup")
    p.add_argument("rule", nargs="?", default="life",
                   help="rule set (default: life)")
    p.add_argument("-g", "--gens", type=int, default=GENERATIONS)
    p.add_argument("--seed", type=int, default=None)
    p.add_argument("--html", action="store_true",
                   help="write an animated life.html instead of animating")
    p.add_argument("-o", "--out", default="life.html")
    p.add_argument("--list", action="store_true", help="list patterns & rules")
    args = p.parse_args(argv)

    if args.list:
        print("\n".join(HELP_LINES))
        return

    pat = args.pattern
    if pat == "soup":            # "soup" == random-ish starting grid
        pat = None
    if pat and pat not in PATTERNS:
        print(f"unknown pattern {pat!r}; known: {', '.join(sorted(PATTERNS))}, soup",
              file=sys.stderr)
        sys.exit(2)
    if args.rule not in RULES:
        print(f"unknown rule {args.rule!r}; known: {', '.join(sorted(RULES))}",
              file=sys.stderr)
        sys.exit(2)

    run(pat, args.rule, args.gens,
        out_html=args.html, out_path=args.out, seed=args.seed)


if __name__ == "__main__":
    main()
