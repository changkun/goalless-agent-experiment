"""CLI entry point for the Game of Life.

Runs in two modes:

- ``--demo`` (default): animate a random soup plus a glider, forever.
- explicit patterns: ``life pulsar glider`` renders one static generation,
  useful for eyeballing shapes.

Generation count is capped by ``-n`` (default 200 for the demo); each render
clears the screen so animation happens in place.
"""

from __future__ import annotations

import argparse
import random
import sys
import time

from .board import render, tick
from .patterns import ALL_PATTERNS, patterns_at

# Keep the viewport slightly narrower than a typical terminal.
DEFAULT_HEIGHT, DEFAULT_WIDTH = 24, 60


def random_soup(height: int, width: int, density: float = 0.15,
                rng: random.Random | None = None) -> set[tuple[int, int]]:
    """A random field of live cells (used as demo background noise)."""
    rng = rng or random.Random()
    return {
        (x, y)
        for y in range(height)
        for x in range(width)
        if rng.random() < density
    }


def animate(cells: set[tuple[int, int]], generations: int, fps: float,
            height: int, width: int) -> None:
    """Run ``generations`` ticks, clearing the screen each frame."""
    delay = 1.0 / fps if fps else 0.0
    live = cells
    for _ in range(generations):
        # \x1b[2J clears the screen, \x1b[H homes the cursor.
        sys.stdout.write("\x1b[2J\x1b[H")
        sys.stdout.write(render(live, height=height, width=width))
        sys.stdout.write(f"\n\ngeneration {_ + 1}/{generations}\n")
        sys.stdout.flush()
        time.sleep(delay)
        live = tick(live)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="life",
        description="Terminal Conway's Game of Life.",
    )
    parser.add_argument(
        "patterns", nargs="*", metavar="PATTERN",
        help="named pattern(s) to show; leave empty for the animated demo",
    )
    parser.add_argument(
        "-n", "--generations", type=int, default=200,
        help="number of generations (demo only; default 200)",
    )
    parser.add_argument(
        "-f", "--fps", type=float, default=8.0,
        help="frames per second in the demo (default 8)",
    )
    parser.add_argument(
        "-s", "--seed", type=int, default=None,
        help="random seed for the demo soup",
    )
    parser.add_argument(
        "--height", type=int, default=DEFAULT_HEIGHT,
        help="viewport height (default 24)",
    )
    parser.add_argument(
        "--width", type=int, default=DEFAULT_WIDTH,
        help="viewport width (default 60)",
    )
    args = parser.parse_args(argv)

    if args.patterns:
        # Static mode: show one generation, no animation.
        for name in args.patterns:
            if name not in ALL_PATTERNS:
                parser.error(f"unknown pattern: {name!r} "
                             f"(known: {', '.join(sorted(ALL_PATTERNS))})")
        cells = patterns_at(dict.fromkeys(args.patterns))  # dedupe, keep order
        print(render(cells, height=args.height, width=args.width))
        return 0

    # Demo mode: random soup with a glider carving through it.
    rng = random.Random(args.seed)
    soup = random_soup(args.height, args.width, rng=rng)
    glider = ALL_PATTERNS["glider"]
    demo = soup | {(x + 6, y + 6) for x, y in glider}
    animate(demo, args.generations, args.fps, args.height, args.width)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
