"""Conway's Game of Life — a tiny, dependency-free implementation."""

from .engine import Board, load_pattern, parse_rle
from .patterns import PATTERNS, get_board

__version__ = "0.1.0"
__all__ = [
    "Board",
    "load_pattern",
    "parse_rle",
    "PATTERNS",
    "get_board",
    "__version__",
]
