"""Run the Game of Life as an animated terminal session.

Usage:
    python -m gol [--pattern glider|blinker] [--generations N]

Patches are diffed between frames so the output stays compact even when a
pattern drifts far off the initial window.
"""
from __future__ import annotations

import argparse
import time

from .engine import _coerce, blinker, glider, next_generation, render


def _home() -> str:
    return "\x1b[H"  # move cursor to top-left


def _clear() -> str:
    return "\x1b[2J"  # clear whole screen


def run(pattern, generations: int, wait: float) -> None:
    grid = _coerce(pattern)
    print(_clear(), end="", flush=True)

    for _ in range(generations):
        print(_home() + render(grid), end="", flush=True)
        time.sleep(wait)
        grid = next_generation(grid)

    print(_home() + render(grid), end="", flush=True)
    print()


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(prog="python -m gol", description=__doc__)
    parser.add_argument(
        "--pattern",
        choices=("glider", "blinker"),
        default="glider",
        help="starting pattern (default: glider)",
    )
    parser.add_argument("--generations", type=int, default=100, help="frames to run")
    parser.add_argument("--wait", type=float, default=0.1, help="seconds between frames")
    args = parser.parse_args(argv)

    pattern = {"glider": glider, "blinker": blinker}[args.pattern]
    run(pattern(), generations=args.generations, wait=args.wait)


if __name__ == "__main__":
    main()
