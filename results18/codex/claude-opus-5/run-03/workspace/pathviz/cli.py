"""Command line interface: generate a maze, then solve and visualize it."""

from __future__ import annotations

import argparse
import sys
import time

from pathviz.grid import Grid
from pathviz.mazes import GENERATORS, generate
from pathviz.render import frames, legend, render
from pathviz.search import ALGORITHMS, SearchResult, search


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="pathviz",
        description="Generate a maze and visualize a pathfinding search in the terminal.",
    )
    parser.add_argument("--width", type=int, default=41, help="grid width (forced odd)")
    parser.add_argument("--height", type=int, default=21, help="grid height (forced odd)")
    parser.add_argument(
        "--maze", choices=GENERATORS, default="backtracker", help="maze generator"
    )
    parser.add_argument("--algo", choices=ALGORITHMS, default="astar", help="search algorithm")
    parser.add_argument("--seed", type=int, default=None, help="seed for reproducible mazes")
    parser.add_argument("--weights", action="store_true", help="add costly terrain patches")
    parser.add_argument("--animate", action="store_true", help="replay the search step by step")
    parser.add_argument("--fps", type=float, default=30.0, help="animation frames per second")
    parser.add_argument("--step", type=int, default=1, help="visits per animation frame")
    parser.add_argument(
        "--compare", action="store_true", help="run every algorithm and print a stats table"
    )
    parser.add_argument("--no-color", action="store_true", help="disable ANSI colors")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    color = not args.no_color and sys.stdout.isatty()
    grid = generate(
        args.width, args.height, kind=args.maze, seed=args.seed, weighted=args.weights
    )

    if args.compare:
        results = [search(grid, algo) for algo in ALGORITHMS]
        print(render(grid, color=color))
        print()
        print(stats_table(results))
        return 0

    result = search(grid, args.algo)
    if args.animate:
        _animate(grid, result, fps=args.fps, step=args.step, color=color)
    else:
        print(render(grid, visited=set(result.visited), path=result.path, color=color))

    print()
    print(legend())
    print(summary(result))
    return 0 if result.found else 1


def _animate(grid: Grid, result: SearchResult, fps: float, step: int, color: bool) -> None:
    delay = 1.0 / fps if fps > 0 else 0.0
    sequence = frames(grid, result, step=step, color=color)
    for frame in sequence:
        sys.stdout.write("\033[H\033[J" if color else "\n")
        sys.stdout.write(frame.text)
        sys.stdout.write(
            f"\n{result.algorithm}  visited {frame.index}/{result.expanded}"
            f"  frontier {frame.frontier}\n"
        )
        sys.stdout.flush()
        if delay:
            time.sleep(delay)


def summary(result: SearchResult) -> str:
    if not result.found:
        return f"{result.algorithm}: no path found after {result.expanded} expansions"
    return (
        f"{result.algorithm}: path {len(result.path)} cells, cost {result.cost}, "
        f"expanded {result.expanded}, peak frontier {result.peak_frontier}"
    )


def stats_table(results: list[SearchResult]) -> str:
    headers = ("algorithm", "path", "cost", "expanded", "peak")
    rows = [
        (
            r.algorithm,
            str(len(r.path)),
            str(r.cost),
            str(r.expanded),
            str(r.peak_frontier),
        )
        for r in results
    ]
    widths = [max(len(h), *(len(row[i]) for row in rows)) for i, h in enumerate(headers)]
    lines = ["  ".join(h.ljust(widths[i]) for i, h in enumerate(headers))]
    lines.append("  ".join("-" * w for w in widths))
    lines.extend("  ".join(col.ljust(widths[i]) for i, col in enumerate(row)) for row in rows)
    return "\n".join(lines)
