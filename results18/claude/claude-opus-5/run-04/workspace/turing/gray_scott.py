"""Gray-Scott reaction-diffusion on a torus, in pure Python.

The Gray-Scott model is two coupled PDEs describing a chemical U being fed
into a dish where it is consumed by V in the autocatalytic reaction
U + 2V -> 3V, while V decays:

    du/dt = Du * lap(u) - u*v^2 + F*(1 - u)
    dv/dt = Dv * lap(v) + u*v^2 - (F + k)*v

F is the feed rate, k the kill rate. Nearly all of the model's famous
behaviour -- spots that divide like cells, labyrinths, coral, travelling
solitons -- lives in a thin sliver of the (F, k) plane; see PRESETS.

There is no numpy here, so the Laplacian is built from whole-list slices
rather than per-cell indexing: every shift is one C-level memcpy, and the
timestep is two list comprehensions. That is roughly 30x faster than the
obvious nested loop and keeps the code shorter, too.
"""

from __future__ import annotations

import random
from dataclasses import dataclass

# (feed, kill) pairs. Anything outside ~0.01 < F < 0.09, 0.03 < k < 0.07
# decays to the trivial uniform state.
PRESETS: dict[str, tuple[float, float]] = {
    "spots": (0.0350, 0.0650),      # isolated dots on a quiet field
    "mitosis": (0.0367, 0.0649),    # dots that grow, pinch, and divide
    "labyrinth": (0.0290, 0.0570),  # space-filling maze of stripes
    "coral": (0.0550, 0.0620),      # branching, tip-splitting growth
    "worms": (0.0540, 0.0630),      # wandering filaments
    "bubbles": (0.0120, 0.0500),    # coarse cells, slow relaxation
    "solitons": (0.0140, 0.0540),   # self-sustaining travelling waves
}


@dataclass
class Grid:
    """The concentration fields, stored as flat row-major lists."""

    width: int
    height: int
    u: list[float]
    v: list[float]

    def __len__(self) -> int:
        return self.width * self.height


def _rows(flat: list[float], width: int) -> list[list[float]]:
    return [flat[i : i + width] for i in range(0, len(flat), width)]


def laplacian(flat: list[float], width: int) -> list[float]:
    """5-point Laplacian with periodic boundaries (a true torus).

    The vertical shifts are plain slices of the flat list. The horizontal
    ones must be done per row -- shifting the flat list by one would wrap
    row r's left edge onto row r-1's right edge, stitching the grid into a
    helix and leaving a visible seam.
    """
    w = width
    up = flat[-w:] + flat[:-w]  # value of the cell above
    down = flat[w:] + flat[:w]  # value of the cell below

    left: list[float] = []
    right: list[float] = []
    for row in _rows(flat, w):
        left += row[-1:] + row[:-1]
        right += row[1:] + row[:1]

    return [
        a + b + c + d - 4.0 * e
        for a, b, c, d, e in zip(up, down, left, right, flat)
    ]


def seeded(
    width: int,
    height: int,
    *,
    seed: int = 0,
    patches: int | None = None,
    radius: int = 4,
) -> Grid:
    """A dish full of U, perturbed by a few square blots of V.

    The uniform state u=1, v=0 is an exact fixed point, so without a
    perturbation nothing ever happens -- but blotting too much of the dish
    is just as fatal: a field that is uniform anywhere has no Laplacian
    there, so an over-seeded grid relaxes straight back to a flat state.
    Hence a patch count proportional to area rather than a fixed one.
    """
    n = width * height
    if patches is None:
        patches = max(1, n // 600)
    u = [1.0] * n
    v = [0.0] * n
    rng = random.Random(seed)

    for _ in range(patches):
        cx = rng.randrange(width)
        cy = rng.randrange(height)
        for dy in range(-radius, radius + 1):
            y = (cy + dy) % height
            for dx in range(-radius, radius + 1):
                x = (cx + dx) % width
                i = y * width + x
                u[i] = 0.50
                v[i] = 0.25 + 0.25 * rng.random()

    return Grid(width, height, u, v)


def step(
    grid: Grid,
    *,
    feed: float,
    kill: float,
    du: float = 0.16,
    dv: float = 0.08,
    dt: float = 1.0,
) -> Grid:
    """Advance one explicit Euler step, in place.

    Stability wants dt * max(du, dv) * 4 <= 1 for the diffusion part, so
    du=0.16 with dt=1.0 sits right at the usual working limit.
    """
    w = grid.width
    u, v = grid.u, grid.v
    lu = laplacian(u, w)
    lv = laplacian(v, w)

    a = dt * du
    b = dt * dv
    f = dt * feed
    fk = dt * (feed + kill)

    grid.u = [
        ui + a * li - dt * ui * vi * vi + f * (1.0 - ui)
        for ui, vi, li in zip(u, v, lu)
    ]
    grid.v = [
        vi + b * li + dt * ui * vi * vi - fk * vi
        for ui, vi, li in zip(u, v, lv)
    ]
    return grid


def simulate(
    width: int,
    height: int,
    *,
    preset: str = "mitosis",
    steps: int = 6000,
    seed: int = 0,
    on_progress=None,
) -> Grid:
    """Run a preset to completion and return the final grid."""
    if preset not in PRESETS:
        raise KeyError(f"unknown preset {preset!r}; try {sorted(PRESETS)}")
    feed, kill = PRESETS[preset]
    grid = seeded(width, height, seed=seed)

    for i in range(steps):
        step(grid, feed=feed, kill=kill)
        if on_progress is not None and (i + 1) % 250 == 0:
            on_progress(i + 1, steps)

    return grid
