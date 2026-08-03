"""Terminal front-end for Conway's Game of Life.

Renders generations to the terminal and (optionally) animates them with a
doubled-space layout so cells look square on a typical terminal font.
"""

from __future__ import annotations

import argparse
import shutil
import sys
import time
from typing import Sequence

from life import Grid
from patterns import PATTERNS


def _draw(grid: Grid, label: str | None) -> None:
    """Print one frame. `label`, when given, is printed above the grid."""
    if label:
        print(f"\x1b[1m{label}\x1b[0m")
    for row in grid.render().splitlines():
        # Double each character so the aspect ratio reads as roughly square.
        print("".join(c * 2 for c in row))


def _pick_pattern(name: str) -> Grid:
    if name in PATTERNS:
        return PATTERNS[name]
    names = ", ".join(sorted(PATTERNS))
    raise SystemExit(f"Unknown pattern {name!r}. Available: {names}")


def run(args: argparse.Namespace) -> int:
    """Entry point shared by `python cli.py` and `python -m life`."""
    grid = _pick_pattern(args.pattern)

    label = (
        f"{args.pattern} — {grid.alive_count()} live cells"
        if args.generations
        else f"{args.pattern} ({grid.rows}×{grid.cols})"
    )

    if args.generations is None:
        # Static mode: just print the pattern once.
        _draw(grid, label)
        print(f"{grid.rows}×{grid.cols} grid, {grid.alive_count()} live cells")
        return 0

    # Animation mode.
    terminal_cols = shutil.get_terminal_size((80, 24)).columns
    # A doubled-character row is 2*cols wide, plus a 1-char right margin.
    cols_fit = (terminal_cols - 1) // 2
    if grid.cols > cols_fit:
        print(
            f"Pattern is {grid.cols} cells wide but terminal only fits ~{cols_fit}; "
            f"shrink the window or pick a smaller pattern.",
            file=sys.stderr,
        )
        return 1

    try:
        for gen in range(args.generations + 1):
            if gen:
                grid.step()
            if args.clear and sys.stdout.isatty():
                # Move the cursor back up to redraw over the previous frame,
                # giving a smooth in-place animation.
                clear = f"\x1b[{grid.rows + 1}A\x1b[2K"  # 2 lines per row + label
                print(clear, end="")
            _draw(grid, f"generation {gen}")
            if gen < args.generations:
                time.sleep(args.delay)
    except KeyboardInterrupt:
        print("\nstopped.", file=sys.stderr)
        return 0
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="life",
        description="Conway's Game of Life in the terminal.",
    )
    parser.add_argument(
        "pattern",
        nargs="?",
        default="glider",
        help="pattern to run (default: glider)",
    )
    parser.add_argument(
        "-n", "--generations",
        type=int,
        metavar="N",
        help="animate for N generations; omit to print the pattern once",
    )
    parser.add_argument(
        "-d", "--delay",
        type=float,
        default=0.15,
        metavar="SEC",
        help="seconds between frames in animation mode (default: 0.15)",
    )
    parser.add_argument(
        "-c", "--clear",
        action="store_true",
        help="redraw each frame in place instead of scrolling (best in a TTY)",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.generations is not None and args.generations < 0:
        raise SystemExit("--generations must be >= 0")
    return run(args)


if __name__ == "__main__":
    sys.exit(main())
