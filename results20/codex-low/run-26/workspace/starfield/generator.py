"""ASCII starfield generator.

Given a width, height and optional seed, produce a text grid of a night sky
with stars rendered at varying brightness using a palette of characters.
"""

from __future__ import annotations

import random

__all__ = ["generate", "DEFAULT_PALETTE", "DEFAULT_DENSITY"]

# Characters ordered from faintest to brightest. The space is used for empty
# cells; the rest map onto star "brightness" levels.
DEFAULT_PALETTE = (".", "*", "+", "o", "O", "*", "#", "@")

DEFAULT_DENSITY = 0.18


def generate(
    width: int,
    height: int,
    *,
    density: float = DEFAULT_DENSITY,
    palette: tuple[str, ...] = DEFAULT_PALETTE,
    seed: int | None = None,
) -> list[str]:
    """Return a list of strings forming an ASCII starfield.

    ``width`` and ``height`` are the grid dimensions in characters. A fresh
    RNG is used internally, so repeated calls are independent unless ``seed``
    is supplied (useful for reproducible output).

    Raises ``ValueError`` for non-positive dimensions, out-of-range density or
    a palette that is not at least two characters long (the first entry marks
    empty cells).
    """
    _validate(width, height, density, palette)
    rng = random.Random(seed)

    # Map each nonzero palette entry to a brightness in [0, 1).
    levels = len(palette) - 1
    stars = len(palette) - 1
    rows: list[str] = []
    for _ in range(height):
        cells: list[str] = []
        for _ in range(width):
            if rng.random() >= density:
                cells.append(palette[0])
                continue
            # Weighted pick so brighter characters are rarer: exponent > 1
            # skews the roll toward the low (faint) end of the palette.
            idx = 1 + int((rng.random() ** 2) * stars) % stars
            cells.append(palette[idx])
        rows.append("".join(cells))
    return rows


def _validate(
    width: int,
    height: int,
    density: float,
    palette: tuple[str, ...],
) -> None:
    if width <= 0 or height <= 0:
        raise ValueError("width and height must be positive")
    if not 0.0 <= density <= 1.0:
        raise ValueError("density must be in the range [0.0, 1.0]")
    if len(palette) < 2:
        raise ValueError("palette must contain at least two characters")
