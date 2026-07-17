"""Step engines and cycle detection for Life-like cellular automata."""

from __future__ import annotations

from .grid import Grid


def parse_rule(spec):
    """Parse 'B3/S23' notation into (birth_set, survive_set)."""
    spec = spec.upper().replace(" ", "")
    if "/" in spec:
        b_part, s_part = spec.split("/", 1)
    else:
        b_part, s_part = spec, ""
    birth = {int(d) for d in b_part.lstrip("B") if d.isdigit()}
    survive = {int(d) for d in s_part.lstrip("S") if d.isdigit()}
    if not birth and not survive:
        raise ValueError(f"could not parse rule spec: {spec!r}")
    return birth, survive


class Simulation:
    """Iterates a Grid under a Life-like rule, with cycle detection."""

    def __init__(self, grid, rule="B3/S23"):
        self.grid = grid
        self.birth, self.survive = parse_rule(rule)
        self.rule = rule
        self.tick_count = 0
        self._history = {}

    def step(self):
        g = self.grid
        w, h, cells = g.w, g.h, g.cells
        new = bytearray(w * h)
        birth, survive = self.birth, self.survive
        for y in range(h):
            base = y * w
            for x in range(w):
                n = g.neighbor_count(x, y)
                idx = base + x
                if cells[idx]:
                    new[idx] = 1 if n in survive else 0
                else:
                    new[idx] = 1 if n in birth else 0
        g.cells = new
        self.tick_count += 1

    def run_until_settled(self, max_ticks=3000):
        """Advance until extinction or a repeated state.

        Returns (outcome, detail):
          ("extinct", tick)         - population reached zero
          ("cycle", (period, tick)) - state repeated; period in ticks
          ("timeout", max_ticks)    - still churning at the cap
        """
        sig = self.grid.signature()
        self._history = {sig: self.tick_count}
        while self.tick_count < max_ticks:
            self.step()
            if self.grid.population() == 0:
                return "extinct", self.tick_count
            sig = self.grid.signature()
            if sig in self._history:
                period = self.tick_count - self._history[sig]
                return "cycle", (period, self.tick_count)
            self._history[sig] = self.tick_count
        return "timeout", max_ticks

    def population_series(self, ticks):
        """Population count at each of the next `ticks` generations."""
        series = []
        for _ in range(ticks):
            self.step()
            series.append(self.grid.population())
        return series


def soup_grid(w, h, density, rng):
    """A random 'soup' - the primordial broth of Life experiments."""
    g = Grid(w, h)
    g.cells = bytearray(
        1 if rng.random() < density else 0 for _ in range(w * h)
    )
    return g


def sparkline(values, width=60):
    """Render a numeric series as a one-line ASCII sparkline."""
    if not values:
        return ""
    blocks = " .:-=+*#%@"
    lo, hi = min(values), max(values)
    span = (hi - lo) or 1
    if len(values) > width:
        bucket = len(values) / width
        sampled = []
        for i in range(width):
            chunk = values[int(i * bucket):int((i + 1) * bucket)]
            sampled.append(sum(chunk) / max(1, len(chunk)))
        values = sampled
    return "".join(
        blocks[min(len(blocks) - 1, int((v - lo) / span * (len(blocks) - 1)))]
        for v in values
    )
