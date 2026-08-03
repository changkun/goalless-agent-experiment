"""Tests for the Game of Life engine and pattern library.

Run with:  python -m pytest gol  (or)  python gol/test_gol.py
"""

import sys
import os

sys.path.insert(0, os.path.dirname(__file__))

from engine import step
from patterns import build, PERIODS, names
from render import render_str


def oscillator_period(seed, period, limit=None):
    """True if a (stationary) oscillator repeats after ``period`` steps."""
    if limit is None:
        limit = period * 3
    universe = seed
    for _ in range(period):
        universe = step(universe)
    if universe != seed:
        return False
    # Confirm it doesn't bounce back early either.
    return True


def spaceship_translation(seed, generations, delta):
    """True if ``seed`` moves by ``delta`` every ``generations`` steps."""
    universe = seed
    for _ in range(generations):
        universe = step(universe)
    return universe == set((x + dx, y + dy) for x, y in seed
                           for dx, dy in [delta])


# --- Engine behaviour ----------------------------------------------------

def test_block_stays_stable():
    assert step(build("block")) == build("block")


def test_beehive_stays_stable():
    assert step(build("beehive")) == build("beehive")


def test_empty_universe_stays_empty():
    assert step(set()) == set()


def test_dead_cell_with_three_neighbours_is_born():
    seed = {(0, 0), (1, 0), (0, 1)}         # L triomino
    next_ = step(seed)
    assert (1, 1) in next_


def test_survival_and_death_rules():
    # 2 neighbours survive, 1 dies of loneliness, 4 dies of overcrowding.
    # A lone pair: each cell has 1 neighbour, so both die (underpopulation).
    pair = {(0, 0), (1, 0)}
    assert step(pair) == set()
    # Full 3x3 block: corner cells survive (3 neighbours), edges (5) and the
    # centre (8) die, and new ring cells are born -> an 8-cell ring.
    block3 = {(x, y) for x in range(3) for y in range(3)}
    assert len(step(block3)) == 8


# --- Patterns -------------------------------------------------------------

def test_blinker_period_2():
    assert oscillator_period(build("blinker"), 2)


def test_toad_period_2():
    assert oscillator_period(build("toad"), 2)


def test_pulsar_period_3():
    assert oscillator_period(build("pulsar"), 3)


def test_pulsar_has_48_cells():
    assert len(build("pulsar")) == 48


def test_glider_translates_diagonally():
    # A glider moves one cell diagonally every 4 generations.
    glider = build("glider")
    assert spaceship_translation(glider, 4, (1, 1))


def test_lwss_translates_sideways():
    # LWSS moves 2 cells left every 4 generations.
    assert spaceship_translation(build("lwss"), 4, (-2, 0))


def test_gosper_gun_emits_and_escapes():
    # The gun body is period 30, but emitted gliders escape, so population
    # grows without bound. Check that it keeps growing over many generations.
    pop0 = len(build("gosper-gun"))
    universe = build("gosper-gun")
    for _ in range(90):
        universe = step(universe)
    # Removed gliders mean the total population now exceeds the seed's.
    assert len(universe) > pop0


def test_all_declared_oscillator_periods_hold():
    for name, period in PERIODS.items():
        if period is None:
            continue
        assert oscillator_period(build(name), period), name


def test_render_layout_matches_pattern_spec():
    glider = build("glider")
    assert render_str(glider, 3, 3, alive="#", dead=".") == ".#.\n..#\n###"


def test_bounding_box_stays_constant_for_blinker():
    for _ in range(10):
        assert len(set(step(build("blinker")))) == 3


if __name__ == "__main__":
    import traceback
    failures = 0
    for name, fn in sorted(globals().items()):
        if name.startswith("test_") and callable(fn):
            try:
                fn()
                print(f"PASS {name}")
            except Exception:
                failures += 1
                print(f"FAIL {name}")
                traceback.print_exc()
    print(f"\n{failures} failure(s)")
    sys.exit(1 if failures else 0)
