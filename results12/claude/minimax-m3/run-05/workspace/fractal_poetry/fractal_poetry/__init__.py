"""
fractal_poetry
==============

A tiny package that prints an ASCII Mandelbrot set and layers a
self-similar poem on top of it. The poem and the fractal share a
structure: each line is the whole made smaller, and the whole is
each line made larger.

Run it:

    python -m fractal_poetry
    # or
    python fractal_poetry/__main__.py
"""

from .mandel import render
from .poem import recite

__all__ = ["render", "recite"]
__version__ = "0.1.0"
