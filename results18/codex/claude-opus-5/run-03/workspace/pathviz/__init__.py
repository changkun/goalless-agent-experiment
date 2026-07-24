"""Terminal maze generation and pathfinding visualization."""

from pathviz.grid import Grid
from pathviz.mazes import generate
from pathviz.search import SearchResult, search

__all__ = ["Grid", "generate", "search", "SearchResult"]
__version__ = "0.1.0"
