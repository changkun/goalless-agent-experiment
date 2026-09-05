"""Conway's Game of Life with RLE pattern support and terminal animation.

Usage:
    python3 life.py                      # Gosper glider gun
    python3 life.py --pattern r-pentomino --steps 200 --fps 20
    python3 life.py --rle 'bo$2bo$3o!' --width 40 --height 20
    python3 life.py --list
"""

from __future__ import annotations

import argparse
import sys
import time

Cells = frozenset[tuple[int, int]]

PATTERNS: dict[str, str] = {
    "glider": "bo$2bo$3o!",
    "blinker": "3o!",
    "r-pentomino": "b2o$2ob$bo!",
    "diehard": "6bob$2o6b$bo3b3o!",
    "acorn": "bo5b$3bo3b$2o2b3o!",
    "gosper-gun": (
        "24bo$22bobo$12b2o6b2o12b2o$11bo3bo4b2o12b2o$2o8bo5bo3b2o$2o8bo3bob2o4b"
        "obo$10bo5bo7bo$11bo3bo$12b2o!"
    ),
    "pulsar": (
        "2b3o3b3o2b$$o4bobo4bo$o4bobo4bo$o4bobo4bo$2b3o3b3o2b$$2b3o3b3o2b$o4bobo"
        "4bo$o4bobo4bo$o4bobo4bo$$2b3o3b3o2b!"
    ),
}


def parse_rle(text: str) -> Cells:
    """Parse a Run Length Encoded pattern into a set of live (x, y) cells.

    Supports the standard tokens: ``b`` (dead), ``o`` (alive), ``$`` (newline),
    ``!`` (end), digit prefixes as run counts, and ``#``/``x =`` header lines.
    """
    cells: set[tuple[int, int]] = set()
    x = y = 0
    run = 0
    for line in text.splitlines() or [text]:
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or stripped.startswith("x"):
            continue
        for char in stripped:
            if char.isdigit():
                run = run * 10 + int(char)
                continue
            count = run or 1
            run = 0
            if char == "b":
                x += count
            elif char == "o":
                cells.update((x + i, y) for i in range(count))
                x += count
            elif char == "$":
                y += count
                x = 0
            elif char == "!":
                return frozenset(cells)
            elif char.isspace():
                continue
            else:
                raise ValueError(f"unexpected RLE token {char!r}")
    return frozenset(cells)


def step(cells: Cells) -> Cells:
    """Advance one generation on an unbounded grid."""
    counts: dict[tuple[int, int], int] = {}
    for x, y in cells:
        for dx in (-1, 0, 1):
            for dy in (-1, 0, 1):
                if dx or dy:
                    key = (x + dx, y + dy)
                    counts[key] = counts.get(key, 0) + 1
    return frozenset(
        pos
        for pos, n in counts.items()
        if n == 3 or (n == 2 and pos in cells)
    )


def translate(cells: Cells, dx: int, dy: int) -> Cells:
    return frozenset((x + dx, y + dy) for x, y in cells)


def bounding_box(cells: Cells) -> tuple[int, int, int, int]:
    """Return (min_x, min_y, max_x, max_y); zeros for an empty set."""
    if not cells:
        return (0, 0, 0, 0)
    xs = [x for x, _ in cells]
    ys = [y for _, y in cells]
    return (min(xs), min(ys), max(xs), max(ys))


def render(cells: Cells, width: int, height: int, alive: str = "█", dead: str = " ") -> str:
    rows = []
    for y in range(height):
        rows.append("".join(alive if (x, y) in cells else dead for x in range(width)))
    return "\n".join(rows)


def centered(cells: Cells, width: int, height: int) -> Cells:
    min_x, min_y, max_x, max_y = bounding_box(cells)
    dx = (width - (max_x - min_x + 1)) // 2 - min_x
    dy = (height - (max_y - min_y + 1)) // 2 - min_y
    return translate(cells, dx, dy)


def animate(cells: Cells, width: int, height: int, steps: int, fps: float) -> None:
    delay = 1 / fps if fps > 0 else 0
    out = sys.stdout
    out.write("\x1b[?25l")
    try:
        for generation in range(steps + 1):
            frame = render(cells, width, height)
            out.write(f"\x1b[H\x1b[2J{frame}\n gen {generation:>5}  alive {len(cells):>5}\n")
            out.flush()
            if generation == steps:
                break
            cells = step(cells)
            if not cells:
                out.write(" everything died.\n")
                break
            time.sleep(delay)
    finally:
        out.write("\x1b[?25h")
        out.flush()


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("--pattern", default="gosper-gun", choices=sorted(PATTERNS))
    parser.add_argument("--rle", help="inline RLE string; overrides --pattern")
    parser.add_argument("--width", type=int, default=80)
    parser.add_argument("--height", type=int, default=30)
    parser.add_argument("--steps", type=int, default=300)
    parser.add_argument("--fps", type=float, default=15)
    parser.add_argument("--list", action="store_true", help="list built-in patterns")
    args = parser.parse_args(argv)

    if args.list:
        for name, rle in PATTERNS.items():
            print(f"{name:14s} {len(parse_rle(rle)):>3} cells   {rle}")
        return 0

    cells = parse_rle(args.rle) if args.rle else parse_rle(PATTERNS[args.pattern])
    if args.rle:
        cells = centered(cells, args.width, args.height)
    else:
        cells = translate(cells, 2, 2)
    try:
        animate(cells, args.width, args.height, args.steps, args.fps)
    except KeyboardInterrupt:
        sys.stdout.write("\x1b[?25h\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
