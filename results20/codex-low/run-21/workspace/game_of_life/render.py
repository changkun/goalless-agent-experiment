"""Terminal rendering for a Game of Life board."""

from __future__ import annotations

from typing import Iterable

from .engine import Board, Point


def cell_to_text(board: Board, x: int, y: int) -> str:
    """Render a single cell position as one character."""
    return "O" if board.is_alive(x, y) else "."


def render(board: Board, *, alive: str = "O", dead: str = ".") -> str:
    """Render the board's bounding box as a string grid.

    Returns an empty string for an empty board.
    """
    bounds = board.bounds()
    if bounds is None:
        return ""
    min_x, min_y, max_x, max_y = bounds
    lines: list[str] = []
    for y in range(min_y, max_y + 1):
        lines.append(
            "".join(alive if board.is_alive(x, y) else dead for x in range(min_x, max_x + 1))
        )
    return "\n".join(lines)


def render_at(board: Board, origin: Point = (0, 0), size: int = 20) -> str:
    """Render a fixed-size window centered on the given origin."""
    width = height = max(1, size)
    start_x = origin[0] - width // 2
    start_y = origin[1] - height // 2
    lines: list[str] = []
    for y in range(start_y, start_y + height):
        lines.append(
            "".join(
                "O" if board.is_alive(x, y) else "."
                for x in range(start_x, start_x + width)
            )
        )
    return "\n".join(lines)
