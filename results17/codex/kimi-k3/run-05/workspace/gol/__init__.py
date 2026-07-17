"""gol - a tiny Game of Life laboratory. Pure stdlib."""

from .grid import Grid
from .sim import Simulation, soup_grid
from . import patterns, palettes

__all__ = ["Grid", "Simulation", "soup_grid", "patterns", "palettes"]
