"""Command-line runner for the maze tool."""

from __future__ import annotations

import argparse
import sys
import time

from .maze import END, PATH, START, VISITED, WALL, Maze

_FRAME = 0.04  # seconds between animation steps


def _parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="maze",
        description="Generate and solve a perfect maze in your terminal.",
    )
    parser.add_argument(
        "rows", type=int, nargs="?", default=12, help="number of rows (cells)"
    )
    parser.add_argument(
        "cols", type=int, nargs="?", default=12, help="number of columns (cells)"
    )
    parser.add_argument(
        "--seed", type=int, default=None, help="RNG seed for reproducible mazes"
    )
    parser.add_argument(
        "--animate", action="store_true", help="animate the solver walking the maze"
    )
    parser.add_argument(
        "--solution", action="store_true", help="show only the solved maze with path"
    )
    return parser.parse_args(argv)


def _with_path(maze: Maze, path: list[tuple[int, int]], cells: set[tuple[int, int]]) -> str:
    """Render the maze, marking visited cells and the final solution path."""
    lines: list[str] = []
    for r in range(maze.rows * 2 + 1):
        line = []
        for c in range(maze.cols * 2 + 1):
            if r % 2 == 1 and c % 2 == 1:  # interior cell
                cell = (r // 2, c // 2)
                if cell == maze.start:
                    line.append(START)
                elif cell == maze.end:
                    line.append(END)
                elif cell in path:
                    line.append(WALL)
                elif cell in cells:
                    line.append(VISITED)
                else:
                    line.append(PATH)
            else:
                line.append(maze.line(r)[c])
        lines.append("".join(line))
    return "\n".join(lines)


def _animate(maze: Maze) -> None:
    """Walk the solution path, printing visited cells as we go."""
    path = maze.solve()
    visited: set[tuple[int, int]] = set()
    frames = []

    for step in path:
        visited.add(step)
        frames.append(_with_path(maze, path, visited))

    # Replay the recorded frames (smooth and deterministic output).
    for frame in frames:
        sys.stdout.write("\033[H\033[2J")  # clear screen
        sys.stdout.write(frame + "\n")
        sys.stdout.flush()
        if len(frames) > 1:
            time.sleep(_FRAME)


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(argv)
    maze = Maze(args.rows, args.cols, seed=args.seed)

    if args.animate:
        _animate(maze)
        return 0

    if args.solution:
        path = maze.solve()
        print(_with_path(maze, path, set(path)))
        return 0

    print(maze.render())

    path = maze.solve()
    print(f"\nPath length: {len(path) - 1} steps")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
