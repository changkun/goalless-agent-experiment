"""CLI: python3 -m turing --preset labyrinth"""

from __future__ import annotations

import argparse
import sys
import time

from .gray_scott import PRESETS, simulate
from .render import RAMPS, to_ppm, to_text


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(
        prog="turing", description="Render Gray-Scott Turing patterns."
    )
    p.add_argument("--preset", default="mitosis", choices=sorted(PRESETS))
    p.add_argument("--width", type=int, default=110)
    p.add_argument("--rows", type=int, default=44, help="output text rows")
    p.add_argument("--steps", type=int, default=6000)
    p.add_argument("--seed", type=int, default=0)
    p.add_argument("--ramp", default="ascii", choices=sorted(RAMPS))
    p.add_argument("--ppm", metavar="PATH", help="also write a P6 image")
    p.add_argument("--quiet", action="store_true")
    args = p.parse_args(argv)

    feed, kill = PRESETS[args.preset]
    # Simulate at 2x vertical resolution; the renderer averages row pairs so
    # that a round spot renders round in a grid of tall character cells.
    height = args.rows * 2
    started = time.monotonic()

    def progress(done: int, total: int) -> None:
        if args.quiet:
            return
        cells = args.width * height * done
        rate = cells / max(time.monotonic() - started, 1e-9) / 1e6
        print(
            f"\r  {done:>6}/{total} steps   {rate:5.2f}M cell-updates/s",
            end="",
            file=sys.stderr,
            flush=True,
        )

    grid = simulate(
        args.width,
        height,
        preset=args.preset,
        steps=args.steps,
        seed=args.seed,
        on_progress=progress,
    )
    if not args.quiet:
        print(file=sys.stderr)

    print(to_text(grid, ramp=args.ramp, factor=2))
    print(
        f"{args.preset}: F={feed:.4f} k={kill:.4f}  "
        f"{args.width}x{height} cells, {args.steps} steps, "
        f"{time.monotonic() - started:.1f}s"
    )
    if args.ppm:
        print(f"wrote {to_ppm(grid, args.ppm)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
