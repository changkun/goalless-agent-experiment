"""ASCII/ANSI rendering of grids and search progress."""

from __future__ import annotations

from dataclasses import dataclass

from pathviz.grid import Cell, Grid
from pathviz.search import SearchResult

WALL_GLYPH = "#"
START_GLYPH = "S"
GOAL_GLYPH = "G"
PATH_GLYPH = "*"
VISITED_GLYPH = "o"
FRONTIER_GLYPH = "+"
#: Floor glyphs indexed by terrain cost tier (1, 2, 3, 4+).
TERRAIN_GLYPHS = (".", ",", ":", ";")

_COLORS = {
    WALL_GLYPH: "90",
    START_GLYPH: "1;96",
    GOAL_GLYPH: "1;95",
    PATH_GLYPH: "1;93",
    VISITED_GLYPH: "34",
    FRONTIER_GLYPH: "1;92",
}
_RESET = "\033[0m"


@dataclass
class Frame:
    """One step of a replayed search."""

    index: int
    text: str
    cell: Cell
    frontier: int


def render(
    grid: Grid,
    visited: set[Cell] | None = None,
    frontier: set[Cell] | None = None,
    path: list[Cell] | None = None,
    color: bool = False,
) -> str:
    """Draw the grid, layering path over frontier over visited over terrain."""
    visited = visited or set()
    frontier = frontier or set()
    path_set = set(path or ())
    lines = []
    for y in range(grid.height):
        row = []
        for x in range(grid.width):
            cell = (x, y)
            row.append(_glyph(grid, cell, visited, frontier, path_set))
        lines.append("".join(_paint(glyph, color) for glyph in row))
    return "\n".join(lines)


def _glyph(
    grid: Grid,
    cell: Cell,
    visited: set[Cell],
    frontier: set[Cell],
    path: set[Cell],
) -> str:
    if cell == grid.start:
        return START_GLYPH
    if cell == grid.goal:
        return GOAL_GLYPH
    if not grid.is_floor(cell):
        return WALL_GLYPH
    if cell in path:
        return PATH_GLYPH
    if cell in frontier:
        return FRONTIER_GLYPH
    if cell in visited:
        return VISITED_GLYPH
    tier = min(grid.weight(cell), len(TERRAIN_GLYPHS)) - 1
    return TERRAIN_GLYPHS[tier]


def _paint(glyph: str, color: bool) -> str:
    if not color or glyph not in _COLORS:
        return glyph
    return f"\033[{_COLORS[glyph]}m{glyph}{_RESET}"


def frames(
    grid: Grid,
    result: SearchResult,
    step: int = 1,
    color: bool = False,
) -> list[Frame]:
    """Replay ``result`` as a list of renderable frames, every ``step`` visits."""
    if step < 1:
        raise ValueError("step must be >= 1")
    out: list[Frame] = []
    visited: set[Cell] = set()
    for index, cell in enumerate(result.visited, start=1):
        visited.add(cell)
        if index % step and index != len(result.visited):
            continue
        edge = _edge(grid, visited)
        out.append(
            Frame(
                index=index,
                text=render(grid, visited=visited, frontier=edge, color=color),
                cell=cell,
                frontier=len(edge),
            )
        )
    final = render(grid, visited=visited, path=result.path, color=color)
    out.append(
        Frame(
            index=len(result.visited),
            text=final,
            cell=grid.goal,
            frontier=0,
        )
    )
    return out


def _edge(grid: Grid, visited: set[Cell]) -> set[Cell]:
    """Floor cells adjacent to the visited set but not yet visited."""
    edge: set[Cell] = set()
    for cell in visited:
        edge.update(n for n in grid.neighbors(cell) if n not in visited)
    return edge


def legend() -> str:
    return (
        f"{WALL_GLYPH} wall   {TERRAIN_GLYPHS[0]} floor (heavier: "
        f"{' '.join(TERRAIN_GLYPHS[1:])})   {VISITED_GLYPH} visited   "
        f"{FRONTIER_GLYPH} frontier   {PATH_GLYPH} path   "
        f"{START_GLYPH} start   {GOAL_GLYPH} goal"
    )
