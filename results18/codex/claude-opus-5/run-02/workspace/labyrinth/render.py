"""Text renderers for carved grids."""

from __future__ import annotations

from .grid import Cell, Grid

WALL, OPEN, TRAIL = 1, 0, 2

_BOX = {
    (False, False, False, False): " ",
    (True, False, False, False): "\u2575",
    (False, True, False, False): "\u2576",
    (False, False, True, False): "\u2577",
    (False, False, False, True): "\u2574",
    (True, True, False, False): "\u2514",
    (True, False, True, False): "\u2502",
    (True, False, False, True): "\u2518",
    (False, True, True, False): "\u250c",
    (False, True, False, True): "\u2500",
    (False, False, True, True): "\u2510",
    (True, True, True, False): "\u251c",
    (True, True, False, True): "\u2534",
    (True, False, True, True): "\u2524",
    (False, True, True, True): "\u252c",
    (True, True, True, True): "\u253c",
}


def wall_bitmap(grid: Grid, path: list[Cell] | None = None) -> list[list[int]]:
    """Expand the grid into a ``(2h+1) x (2w+1)`` map of walls, floors and trail."""
    rows, cols = 2 * grid.height + 1, 2 * grid.width + 1
    bitmap = [[WALL] * cols for _ in range(rows)]
    trail = set(path or ())
    for cell in grid.cells():
        row, col = cell
        y, x = 2 * row + 1, 2 * col + 1
        bitmap[y][x] = TRAIL if cell in trail else OPEN
        for other in grid.passages(cell):
            my, mx = y + (other[0] - row), x + (other[1] - col)
            both = cell in trail and other in trail
            bitmap[my][mx] = TRAIL if both else OPEN
    return bitmap


def render_blocks(grid: Grid, path: list[Cell] | None = None) -> str:
    """Solid block walls; two columns per cell so output looks square."""
    glyphs = {WALL: "\u2588\u2588", OPEN: "  ", TRAIL: "\u00b7\u00b7"}
    return "\n".join(
        "".join(glyphs[value] for value in row) for row in wall_bitmap(grid, path)
    )


def render_ascii(grid: Grid, path: list[Cell] | None = None) -> str:
    """Portable ``+---+`` rendering, ideal for diffing and doctests."""
    glyphs = {OPEN: "   ", TRAIL: " * "}
    lines = ["+" + "---+" * grid.width]
    for row in range(grid.height):
        top, bottom = "|", "+"
        for col in range(grid.width):
            cell = (row, col)
            body = glyphs[TRAIL if path and cell in path else OPEN]
            east = (row, col + 1)
            top += body + (" " if grid.linked(cell, east) else "|")
            south = (row + 1, col)
            bottom += ("   " if grid.linked(cell, south) else "---") + "+"
        lines.append(top)
        lines.append(bottom)
    return "\n".join(lines)


def render_box(grid: Grid, path: list[Cell] | None = None) -> str:
    """Box-drawing characters: compact and pretty in a modern terminal."""
    bitmap = wall_bitmap(grid, path)
    height, width = len(bitmap), len(bitmap[0])

    def is_wall(y: int, x: int) -> bool:
        return 0 <= y < height and 0 <= x < width and bitmap[y][x] == WALL

    lines = []
    for y in range(height):
        line = []
        for x in range(width):
            if bitmap[y][x] == TRAIL:
                line.append("\u00b7")
            elif bitmap[y][x] == OPEN:
                line.append(" ")
            else:
                key = (is_wall(y - 1, x), is_wall(y, x + 1), is_wall(y + 1, x), is_wall(y, x - 1))
                glyph = _BOX[key]
                line.append(glyph if glyph != " " else "\u25aa")
            line.append(glyph_filler(bitmap, y, x))
        lines.append("".join(line).rstrip())
    return "\n".join(lines)


def glyph_filler(bitmap: list[list[int]], y: int, x: int) -> str:
    """Horizontal padding so box output keeps a roughly square aspect ratio."""
    if x + 1 >= len(bitmap[0]):
        return ""
    left, right = bitmap[y][x], bitmap[y][x + 1]
    if left == WALL and right == WALL:
        return "\u2500"
    if TRAIL in (left, right) and WALL not in (left, right):
        return "\u00b7"
    return " "


RENDERERS = {
    "blocks": render_blocks,
    "ascii": render_ascii,
    "box": render_box,
}
