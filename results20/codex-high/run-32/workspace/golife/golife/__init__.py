"""golife — Conway's Game of Life for the terminal."""
from .engine import Universe, Pattern
from . import patterns

__all__ = ["Universe", "Pattern", "patterns"]
__version__ = "0.1.0"
