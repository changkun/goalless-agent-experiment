#!/usr/bin/env python3
"""Command line front-end: python3 cli.py [sample] [options]"""

from __future__ import annotations

import argparse
import sys

from samples import SAMPLES
from wfc import Contradiction, generate

RESET = "\033[0m"


def colourise(rows: list[str], palette: dict[str, int]) -> list[str]:
    """Wrap each run of like-coloured characters in one ANSI escape."""
    if not palette:
        return rows
    out = []
    for row in rows:
        parts, current = [], None
        for char in row:
            colour = palette.get(char)
            if colour != current:
                parts.append(RESET if colour is None else f"\033[38;5;{colour}m")
                current = colour
            parts.append(char)
        parts.append(RESET)
        out.append("".join(parts))
    return out


def emit(title: str, rows: list[str], palette: dict[str, int], colour: bool) -> None:
    print(f"\n\033[1m{title}\033[0m" if colour else f"\n{title}")
    for row in colourise(rows, palette) if colour else rows:
        print(f"  {row}")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Synthesise ASCII textures with wave function collapse.",
        epilog="samples: " + ", ".join(SAMPLES),
    )
    parser.add_argument("sample", nargs="?", default="island", choices=[*SAMPLES, "all"])
    parser.add_argument("-w", "--width", type=int, default=72)
    parser.add_argument("-H", "--height", type=int, default=20)
    parser.add_argument("-n", "--size", type=int, help="pattern size (default: per sample)")
    parser.add_argument("-s", "--seed", type=int, default=None)
    parser.add_argument("--periodic", action="store_true", help="make the output tileable")
    parser.add_argument("--show-sample", action="store_true", help="also print the input")
    parser.add_argument("--no-color", dest="colour", action="store_false")
    parser.add_argument("--list", action="store_true", help="describe the samples and exit")
    args = parser.parse_args(argv)

    if args.list:
        for sample in SAMPLES.values():
            rows, cols = len(sample.rows), len(sample.rows[0])
            print(f"  {sample.name:<10} {rows}x{cols}, N={sample.size}  — {sample.blurb}")
        return 0

    names = list(SAMPLES) if args.sample == "all" else [args.sample]
    status = 0
    for name in names:
        sample = SAMPLES[name]
        if args.show_sample:
            emit(f"{name} (sample)", list(sample.rows), sample.palette, args.colour)
        try:
            rows = generate(
                list(sample.rows),
                args.width,
                args.height,
                size=args.size or sample.size,
                symmetry=sample.symmetry,
                periodic_input=sample.periodic_input,
                periodic_output=args.periodic,
                seed=args.seed,
            )
        except Contradiction as exc:
            print(f"\n{name}: {exc}", file=sys.stderr)
            status = 1
            continue
        emit(f"{name} — {sample.blurb}", rows, sample.palette, args.colour)
    return status


if __name__ == "__main__":
    raise SystemExit(main())
