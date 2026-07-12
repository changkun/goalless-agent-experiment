"""ASCII Mandelbrot renderer. No dependencies, just stdlib + complex numbers."""

from __future__ import annotations

# A short ramp from "inside the set" to "diverged fast". The exact
# characters don't matter — what matters is that the eye can read the
# coastline.
_RAMP = " .:-=+*#%@"


def render(
    width: int = 78,
    height: int = 32,
    max_iter: int = 80,
    *,
    x_min: float = -2.2,
    x_max: float = 0.8,
    y_min: float = -1.2,
    y_max: float = 1.2,
) -> str:
    """Return a string of an ASCII Mandelbrot set, `width` x `height`.

    Each cell is one character. Pixels inside the set are spaces; pixels
    outside are picked from a short ramp based on escape iteration count.
    """
    if width < 4 or height < 4:
        raise ValueError("width and height must be at least 4")
    if max_iter < 4:
        raise ValueError("max_iter must be at least 4")

    rows: list[str] = []
    dx = (x_max - x_min) / width
    dy = (y_max - y_min) / height
    # Slight vertical squish because terminal cells are taller than wide.
    for j in range(height):
        row: list[str] = []
        for i in range(width):
            c = complex(x_min + i * dx, y_max - j * dy)
            row.append(_escape_char(c, max_iter))
        rows.append("".join(row))
    return "\n".join(rows)


def _escape_char(c: complex, max_iter: int) -> str:
    z = 0j
    for n in range(max_iter):
        z = z * z + c
        if abs(z) > 2.0:
            # Map iteration count to a ramp index. Inside the set, n
            # would reach max_iter and we fall through to a space.
            idx = int(n * (len(_RAMP) - 1) / max_iter)
            return _RAMP[idx]
    return " "
