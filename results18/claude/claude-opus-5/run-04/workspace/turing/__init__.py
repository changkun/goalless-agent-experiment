"""Turing patterns from the Gray-Scott reaction-diffusion model."""

from .gray_scott import PRESETS, Grid, laplacian, seeded, simulate, step
from .render import RAMPS, to_ppm, to_text

__all__ = [
    "PRESETS",
    "RAMPS",
    "Grid",
    "laplacian",
    "seeded",
    "simulate",
    "step",
    "to_ppm",
    "to_text",
]
