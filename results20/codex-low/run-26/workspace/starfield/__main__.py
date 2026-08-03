"""Command line entry point: ``python -m starfield --help``."""

from __future__ import annotations

import argparse
import sys

from .generator import DEFAULT_DENSITY, DEFAULT_PALETTE, generate

CELL = "\u2588"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="starfield",
        description="Print a random ASCII night sky.",
    )
    parser.add_argument(
        "width", type=int, nargs="?", default=80, help="number of columns (default: 80)"
    )
    parser.add_argument(
        "height", type=int, nargs="?", default=24, help="number of rows (default: 24)"
    )
    parser.add_argument(
        "-d",
        "--density",
        type=float,
        default=DEFAULT_DENSITY,
        help=f"star density, 0.0-1.0 (default: {DEFAULT_DENSITY})",
    )
    parser.add_argument(
        "--seed", type=int, default=None, help="RNG seed for reproducible output"
    )
    parser.add_argument(
        "--full-block",
        action="store_true",
        help="render the grid with full block characters (U+2588)",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        rows = generate(
            args.width, args.height, density=args.density, seed=args.seed
        )
    except ValueError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2

    if args.full_block:
        cells = {c: CELL for c in set("".join(rows)) - {" "}}
        rows = ["".join(cells.get(ch, " ") for ch in row) for row in rows]

    print("\n".join(rows))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
