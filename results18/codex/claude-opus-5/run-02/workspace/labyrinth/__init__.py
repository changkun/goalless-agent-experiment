"""Labyrinth: generate, solve and render mazes in the terminal."""

from .generators import (
    GENERATORS,
    binary_tree,
    braid,
    randomized_kruskal,
    randomized_prim,
    recursive_backtracker,
)
from .grid import Grid
from .render import RENDERERS, render_ascii, render_blocks, render_box
from .solvers import dead_ends, flood, is_perfect, longest_path, shortest_path, stats

__all__ = [
    "GENERATORS",
    "RENDERERS",
    "Grid",
    "binary_tree",
    "braid",
    "dead_ends",
    "flood",
    "is_perfect",
    "longest_path",
    "randomized_kruskal",
    "randomized_prim",
    "recursive_backtracker",
    "render_ascii",
    "render_blocks",
    "render_box",
    "shortest_path",
    "stats",
]
__version__ = "0.1.0"
