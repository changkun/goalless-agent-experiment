"""Command-line interface for the Game of Life."""

from __future__ import annotations

import argparse
import random
import sys
import time

from .engine import PRESETS, Game


def _random_live(width: int, height: int, density: float) -> set[tuple[int, int]]:
    rng = random.Random()
    return {
        (r, c)
        for r in range(height)
        for c in range(width)
        if rng.random() < density
    }


def _parse_pattern_arg(game: Game, text: str) -> None:
    for r, line in enumerate(text.splitlines()):
        for c, ch in enumerate(line):
            if ch in "Oo#Xx*":
                nr, nc = r, c
                if 0 <= nr < game.height and 0 <= nc < game.width:
                    game.live.add((nr, nc))
    game.generation = 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="life",
        description="Conway's Game of Life in pure Python.",
    )
    parser.add_argument("--width", type=int, default=40, help="board width (default 40)")
    parser.add_argument("--height", type=int, default=20, help="board height (default 20)")
    parser.add_argument(
        "--pattern",
        choices=sorted(PRESETS),
        default=None,
        help="start from a classic pattern",
    )
    parser.add_argument(
        "--random",
        action="store_true",
        help="seed the board with random live cells",
    )
    parser.add_argument("--density", type=float, default=0.3, help="density for --random (default 0.3)")
    parser.add_argument(
        "--generations",
        type=int,
        default=50,
        help="number of generations to run (default 50)",
    )
    parser.add_argument(
        "--interval",
        type=float,
        default=0.1,
        help="seconds between frames (default 0.1)",
    )
    parser.add_argument(
        "--wrap",
        action="store_true",
        help="wrap edges (toroidal board)",
    )
    parser.add_argument(
        "--single",
        action="store_true",
        help="print a single static frame instead of animating",
    )
    parser.add_argument(
        "--pattern-text",
        default=None,
        help="load a pattern from a literal string of O and . characters",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)

    game = Game(args.width, args.height, wrap=args.wrap)
    if args.pattern:
        game.load(args.pattern)
    elif args.random:
        game.live = _random_live(args.width, args.height, args.density)
        game._trim()
    elif args.pattern_text:
        _parse_pattern_arg(game, args.pattern_text)
    else:
        game.load("glider")

    if args.single:
        print(game.board())
        print(f"\ngeneration={game.generation} population={game.population()}")
        return 0

    try:
        for _ in range(args.generations):
            print("\033[2J\033[H" + game.board())
            print(f"generation={game.generation} population={game.population()}")
            sys.stdout.flush()
            if game.population() == 0:
                break
            time.sleep(args.interval)
            game.step()
    except KeyboardInterrupt:
        pass
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
