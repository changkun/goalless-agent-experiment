"""Turn a concentration field into something you can see in a terminal."""

from __future__ import annotations

from .gray_scott import Grid

# Dark-to-light ramps. Terminal cells are about twice as tall as they are
# wide, so the renderer averages vertical pairs of simulation cells to keep
# circles looking circular (see `squash`).
RAMPS = {
    "ascii": " .:-=+*#%@",
    "blocks": " ░▒▓█",
    "shades": " ·∶≡▒▓█",
}


def squash(grid: Grid, factor: int = 2) -> tuple[list[float], int, int]:
    """Average every `factor` rows together to correct character aspect."""
    if factor < 1:
        raise ValueError("factor must be >= 1")
    w, h = grid.width, grid.height
    rows = h // factor
    out: list[float] = []
    for r in range(rows):
        base = r * factor * w
        for x in range(w):
            out.append(
                sum(grid.v[base + k * w + x] for k in range(factor)) / factor
            )
    return out, w, rows


def to_text(grid: Grid, *, ramp: str = "ascii", factor: int = 2) -> str:
    """Render the V field as a block of characters.

    Levels are stretched to the frame's own min/max: a pattern that has
    settled into a narrow band of concentrations still shows its structure.
    """
    chars = RAMPS.get(ramp, ramp)
    field, w, rows = squash(grid, factor)

    lo, hi = min(field), max(field)
    span = hi - lo
    if span < 1e-12:
        return "\n".join(chars[0] * w for _ in range(rows))

    last = len(chars) - 1
    scale = last / span
    lines = []
    for r in range(rows):
        row = field[r * w : (r + 1) * w]
        lines.append("".join(chars[int((x - lo) * scale + 0.5)] for x in row))
    return "\n".join(lines)


def to_ppm(grid: Grid, path: str) -> str:
    """Write the V field as a binary PPM (P6) -- no image library needed."""
    w, h = grid.width, grid.height
    lo, hi = min(grid.v), max(grid.v)
    span = (hi - lo) or 1.0

    data = bytearray()
    for value in grid.v:
        t = (value - lo) / span
        # A cool-to-warm ramp: deep indigo -> teal -> cream.
        data += bytes(
            (
                int(255 * min(1.0, max(0.0, 1.6 * t - 0.35))),
                int(255 * min(1.0, max(0.0, 1.25 * t))),
                int(255 * min(1.0, max(0.0, 0.35 + 0.55 * t))),
            )
        )

    with open(path, "wb") as fh:
        fh.write(b"P6\n%d %d\n255\n" % (w, h))
        fh.write(data)
    return path
