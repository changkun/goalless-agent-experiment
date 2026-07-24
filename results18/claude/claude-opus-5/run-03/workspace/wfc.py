"""Overlapping-model Wave Function Collapse for ASCII textures.

Given a small sample grid of characters, WFC synthesises a larger grid in which
every NxN window also appears somewhere in the sample. The result is locally
indistinguishable from the input and globally novel.

The algorithm is the classic observe/propagate loop:

  1. Every output cell starts as a superposition of all NxN patterns.
  2. Observe: collapse the cell with the lowest Shannon entropy to a single
     pattern, chosen with probability proportional to its frequency in the sample.
  3. Propagate: remove every pattern that lost its last supporting neighbour,
     using incrementally maintained support counts (Gumin's propagator).
  4. Repeat until fully collapsed, or restart if a cell runs out of options.

No dependencies. See samples.py for inputs and cli.py for the entry point.
"""

from __future__ import annotations

import math
import random
from dataclasses import dataclass

# Cardinal directions as (dx, dy). Index i is opposite to index i ^ 2.
DIRECTIONS = ((-1, 0), (0, -1), (1, 0), (0, 1))


def opposite(direction: int) -> int:
    return direction ^ 2


class Contradiction(Exception):
    """Raised when a cell's superposition collapses to nothing."""


Pattern = tuple[str, ...]  # N rows of N characters, flattened per row


@dataclass(frozen=True)
class PatternSet:
    """The NxN patterns extracted from a sample, plus their adjacency rules."""

    size: int
    patterns: tuple[Pattern, ...]
    weights: tuple[int, ...]
    # propagator[d][t] = patterns that may sit at offset DIRECTIONS[d] from t
    propagator: tuple[tuple[tuple[int, ...], ...], ...]

    def __len__(self) -> int:
        return len(self.patterns)

    def char_at(self, pattern_index: int, x: int, y: int) -> str:
        return self.patterns[pattern_index][y][x]


def _reflect(rows: list[str]) -> list[str]:
    return [row[::-1] for row in rows]


def _rotate(rows: list[str]) -> list[str]:
    """Rotate 90 degrees clockwise."""
    return ["".join(col) for col in zip(*reversed(rows))]


def _variants(rows: list[str], symmetry: int) -> list[list[str]]:
    """Up to 8 dihedral variants of a grid, in the usual r/reflect order."""
    out: list[list[str]] = []
    current = rows
    for _ in range(4):
        out.append(current)
        out.append(_reflect(current))
        current = _rotate(current)
    return out[:symmetry]


def build_patterns(
    sample: list[str],
    size: int = 3,
    *,
    symmetry: int = 8,
    periodic_input: bool = True,
) -> PatternSet:
    """Extract every NxN window of `sample` (with symmetries) and its adjacencies."""
    if size < 1:
        raise ValueError("pattern size must be >= 1")
    height = len(sample)
    width = len(sample[0])
    if any(len(row) != width for row in sample):
        raise ValueError("sample rows must all be the same length")
    if not periodic_input and (height < size or width < size):
        raise ValueError("sample is smaller than the pattern size")

    counts: dict[Pattern, int] = {}
    limit_y = height if periodic_input else height - size + 1
    limit_x = width if periodic_input else width - size + 1
    for y in range(limit_y):
        for x in range(limit_x):
            window = [
                "".join(sample[(y + dy) % height][(x + dx) % width] for dx in range(size))
                for dy in range(size)
            ]
            for variant in _variants(window, symmetry):
                key = tuple(variant)
                counts[key] = counts.get(key, 0) + 1

    patterns = tuple(counts)
    weights = tuple(counts[p] for p in patterns)

    # Two patterns agree in direction d if their overlapping cells match.
    def agrees(a: Pattern, b: Pattern, dx: int, dy: int) -> bool:
        xmin, xmax = (0, size + dx) if dx < 0 else (dx, size)
        ymin, ymax = (0, size + dy) if dy < 0 else (dy, size)
        for y in range(ymin, ymax):
            for x in range(xmin, xmax):
                if a[y][x] != b[y - dy][x - dx]:
                    return False
        return True

    propagator = tuple(
        tuple(
            tuple(t2 for t2, b in enumerate(patterns) if agrees(a, b, dx, dy))
            for a in patterns
        )
        for dx, dy in DIRECTIONS
    )
    return PatternSet(size, patterns, weights, propagator)


class Wave:
    """The output grid as a superposition of patterns, with entropy bookkeeping."""

    def __init__(self, pattern_set: PatternSet, width: int, height: int, periodic: bool):
        self.ps = pattern_set
        self.width = width
        self.height = height
        self.periodic = periodic
        count = len(pattern_set)
        cells = width * height

        self.wave = [[True] * count for _ in range(cells)]
        # support[cell][pattern][d]: how many patterns still live in the neighbour
        # at DIRECTIONS[d] that would permit this pattern here. When it hits zero
        # the pattern has lost all support from that side and must be banned.
        self.support = [
            [[len(pattern_set.propagator[d][t]) for d in range(4)] for t in range(count)]
            for _ in range(cells)
        ]
        self.options = [count] * cells

        weights = pattern_set.weights
        self._w_log_w = [w * math.log(w) for w in weights]
        total = float(sum(weights))
        total_log = sum(self._w_log_w)
        self.sum_weights = [total] * cells
        self.sum_w_log_w = [total_log] * cells
        self.entropy = [math.log(total) - total_log / total] * cells

        self._stack: list[tuple[int, int]] = []
        self._seed_unsupported()

    def _seed_unsupported(self) -> None:
        """Ban patterns that start with no support at all in some direction.

        A pattern extracted from a non-periodic sample can have an empty
        propagator entry — nothing may legally follow it that way. Such a
        pattern is unusable in any cell that actually has a neighbour there, and
        nothing in the propagate loop would ever remove it (its support count
        starts at zero, so it can never *reach* zero). Ban it up front.
        """
        starved = [
            [t for t in range(len(self.ps)) if not self.ps.propagator[d][t]]
            for d in range(4)
        ]
        if not any(starved):
            return
        for cell in range(self.width * self.height):
            for d in range(4):
                if starved[d] and self.neighbour(cell, d) is not None:
                    for t in starved[d]:
                        self.ban(cell, t)

    def neighbour(self, cell: int, direction: int) -> int | None:
        dx, dy = DIRECTIONS[direction]
        x = cell % self.width + dx
        y = cell // self.width + dy
        if self.periodic:
            return (y % self.height) * self.width + (x % self.width)
        if 0 <= x < self.width and 0 <= y < self.height:
            return y * self.width + x
        return None

    def ban(self, cell: int, pattern: int) -> None:
        if not self.wave[cell][pattern]:
            return
        self.wave[cell][pattern] = False
        self.options[cell] -= 1
        if self.options[cell] == 0:
            raise Contradiction(f"cell {cell} has no valid patterns")

        self.sum_weights[cell] -= self.ps.weights[pattern]
        self.sum_w_log_w[cell] -= self._w_log_w[pattern]
        total = self.sum_weights[cell]
        self.entropy[cell] = math.log(total) - self.sum_w_log_w[cell] / total
        self._stack.append((cell, pattern))

    def propagate(self) -> None:
        while self._stack:
            cell, pattern = self._stack.pop()
            for d in range(4):
                neighbour = self.neighbour(cell, d)
                if neighbour is None:
                    continue
                back = opposite(d)
                for t in self.ps.propagator[d][pattern]:
                    counts = self.support[neighbour][t]
                    counts[back] -= 1
                    if counts[back] == 0:
                        self.ban(neighbour, t)

    def lowest_entropy_cell(self, rng: random.Random) -> int | None:
        """The undecided cell closest to collapsing; None when fully collapsed."""
        best = None
        best_score = math.inf
        for cell in range(len(self.wave)):
            if self.options[cell] <= 1:
                continue
            # Tiny jitter breaks ties without biasing toward low indices.
            score = self.entropy[cell] + rng.random() * 1e-6
            if score < best_score:
                best_score, best = score, cell
        return best

    def observe(self, cell: int, rng: random.Random) -> None:
        allowed = [t for t, ok in enumerate(self.wave[cell]) if ok]
        chosen = rng.choices(allowed, weights=[self.ps.weights[t] for t in allowed])[0]
        for t in allowed:
            if t != chosen:
                self.ban(cell, t)

    def collapsed_pattern(self, cell: int) -> int:
        return self.wave[cell].index(True)


def _attempt(
    ps: PatternSet, width: int, height: int, periodic: bool, rng: random.Random
) -> Wave:
    wave = Wave(ps, width, height, periodic)
    wave.propagate()  # settles non-periodic boundary constraints
    while (cell := wave.lowest_entropy_cell(rng)) is not None:
        wave.observe(cell, rng)
        wave.propagate()
    return wave


def render(wave: Wave) -> list[str]:
    """Flatten a collapsed wave into character rows.

    Each cell contributes its pattern's top-left character. For a non-periodic
    output the final row and column of cells contribute their whole pattern, so
    nothing is cropped.
    """
    ps = wave.ps
    n = ps.size
    pad = 0 if wave.periodic else n - 1
    out = [[" "] * (wave.width + pad) for _ in range(wave.height + pad)]
    for y in range(wave.height):
        for x in range(wave.width):
            t = wave.collapsed_pattern(y * wave.width + x)
            span_x = n if (pad and x == wave.width - 1) else 1
            span_y = n if (pad and y == wave.height - 1) else 1
            for dy in range(span_y):
                for dx in range(span_x):
                    out[y + dy][x + dx] = ps.char_at(t, dx, dy)
    return ["".join(row) for row in out]


def generate(
    sample: list[str],
    width: int,
    height: int,
    *,
    size: int = 3,
    symmetry: int = 8,
    periodic_input: bool = True,
    periodic_output: bool = False,
    seed: int | None = None,
    attempts: int = 40,
) -> list[str]:
    """Synthesise a `width` x `height` grid whose NxN windows all occur in `sample`.

    Raises Contradiction if no attempt succeeds.
    """
    ps = build_patterns(sample, size, symmetry=symmetry, periodic_input=periodic_input)
    cells_w = width if periodic_output else max(1, width - size + 1)
    cells_h = height if periodic_output else max(1, height - size + 1)

    root = random.Random(seed)
    last: Contradiction | None = None
    for _ in range(attempts):
        rng = random.Random(root.getrandbits(64))
        try:
            return render(_attempt(ps, cells_w, cells_h, periodic_output, rng))
        except Contradiction as exc:  # over-constrained draw; reroll
            last = exc
    raise Contradiction(f"no solution in {attempts} attempts (last: {last})")
