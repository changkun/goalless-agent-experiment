"""Terminal animation for Conway's Game of Life."""

from __future__ import annotations

import argparse
import shutil
import sys
import time

from .engine import Board
from .patterns import PATTERNS


def render(board: Board, width: int, height: int) -> str:
    """Render the live cells within a width x height window as text."""
    grid = [[" "] * width for _ in range(height)]
    for x, y in board:
        if 0 <= x < width and 0 <= y < height:
            grid[y][x] = "#"
    return "\n".join("".join(row) for row in grid)


def centered_offset(board: Board, width: int, height: int) -> tuple[int, int]:
    """Compute an (dx, dy) shift that centers the board's live cells."""
    box = board.bounding_box()
    if box is None:
        return 0, 0
    min_x, min_y, max_x, max_y = box
    pattern_width = max_x - min_x + 1
    pattern_height = max_y - min_y + 1
    dx = (width - pattern_width) // 2 - min_x
    dy = (height - pattern_height) // 2 - min_y
    return dx, dy


def run(pattern_name: str, generations: int, delay: float) -> None:
    if pattern_name not in PATTERNS:
        available = ", ".join(sorted(PATTERNS))
        raise SystemExit(f"Unknown pattern '{pattern_name}'. Choose from: {available}")

    term_size = shutil.get_terminal_size(fallback=(80, 24))
    width, height = term_size.columns, max(term_size.lines - 2, 5)

    board = Board.from_coordinates(PATTERNS[pattern_name])
    dx, dy = centered_offset(board, width, height)
    board = board.translated(dx, dy)

    clear_screen = "\033[H\033[J"
    for generation in range(generations):
        sys.stdout.write(clear_screen)
        sys.stdout.write(render(board, width, height))
        sys.stdout.write(f"\nGeneration {generation + 1}/{generations} - {pattern_name}\n")
        sys.stdout.flush()
        time.sleep(delay)
        board = board.step()


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Animate Conway's Game of Life in your terminal.")
    parser.add_argument(
        "pattern",
        nargs="?",
        default="glider",
        choices=sorted(PATTERNS),
        help="Starting pattern to animate (default: glider).",
    )
    parser.add_argument(
        "-g", "--generations",
        type=int,
        default=60,
        help="Number of generations to simulate (default: 60).",
    )
    parser.add_argument(
        "-d", "--delay",
        type=float,
        default=0.1,
        help="Seconds to pause between generations (default: 0.1).",
    )
    args = parser.parse_args(argv)
    run(args.pattern, args.generations, args.delay)


if __name__ == "__main__":
    main()
