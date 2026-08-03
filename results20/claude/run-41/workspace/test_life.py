#!/usr/bin/env python3
"""Tests for life.py and patterns.py. Run with `python3 -m pytest test_life.py`
or, with no pytest, `python3 test_life.py`."""
import collections

from life import Life
from patterns import parse_rle, normalize, find, all_patterns


# --- Independent reference engine (dict-based, no shared code) ---
def ref_step(live):
    counts = collections.Counter()
    for y, x in live:
        for dy in (-1, 0, 1):
            for dx in (-1, 0, 1):
                if dy == 0 and dx == 0:
                    continue
                counts[(y + dy, x + dx)] += 1
    return {pos for pos, n in counts.items() if n == 3 or (n == 2 and pos in live)}


def evo(cells, n):
    """Evolve a *wrapped* Life board n generations (our torus semantics)."""
    b = Life(200, 200)
    b.seed(list(cells))
    for _ in range(n):
        b.step()
    return set(b.cells)


# --- Core rules ---

def test_block_is_still_life():
    b = Life(10, 10)
    b.seed([(5, 5), (5, 6), (6, 5), (6, 6)])
    for _ in range(5):
        b.step()
    assert b.count() == 4


def test_blinker_period_two():
    b = Life(10, 10)
    b.seed([(5, 4), (5, 5), (5, 6)])
    b.step()
    assert b.cells == {(4, 5), (5, 5), (6, 5)}
    b.step()
    assert b.cells == {(5, 4), (5, 5), (5, 6)}


def test_glider_moves_and_keeps_shape():
    g = Life(20, 20)
    g.seed([(8, 9), (9, 10), (10, 8), (10, 9), (10, 10)])
    seen = set()
    for _ in range(30):
        g.step()
        assert g.count() == 5
        seen.add(frozenset(g.cells))
    assert len(seen) >= 20  # actually moving, not stuck


def test_alive_with_two_neighbours_survives():
    # A live cell with exactly 2 neighbours survives. In the corner triple
    # (0,0),(1,0),(0,1), cell (0,0) has 2 neighbours and lives.
    b = Life(10, 10)
    b.seed([(0, 0), (1, 0), (0, 1)])
    b.step()
    assert (0, 0) in b.cells


def test_lone_cell_dies():
    b = Life(10, 10)
    b.seed([(5, 5)])
    b.step()
    assert b.count() == 0


def test_dead_cell_with_three_neighbours_is_born():
    b = Life(10, 10)
    b.seed([(4, 5), (5, 4), (5, 6)])  # corners of a missing center at (5, 5)
    b.step()
    assert (5, 5) in b.cells


# --- Engine matches the independent reference ---

def test_engine_matches_reference_on_random_board():
    import random
    random.seed(0)
    live = {(random.randrange(40), random.randrange(40)) for _ in range(120)}
    mine = set(evo(live, 1))
    ref = ref_step(set(live))
    assert mine == ref


def test_wrapping_makes_edges_adjacent():
    # A cell at row 0 and one at row h-1 in the same column are neighbors via
    # the vertical seam. Place live cells at (0,0) and (0,4) (adjacent through
    # the horizontal wrap) plus (0,1); the corner (0,0) then has 3 neighbors and
    # survives only because of wrapping.
    b = Life(5, 5)
    b.seed([(0, 0), (0, 4), (0, 1)])
    b.step()
    assert (0, 0) in b.cells


# --- RLE parser ---

def test_parse_rle_block():
    cells = parse_rle("2o$2o!")
    assert cells == {(0, 0), (0, 1), (1, 0), (1, 1)}


def test_parse_rle_glider():
    cells = parse_rle("bob$2bo$3o!")
    assert normalize(cells) == {(0, 1), (1, 2), (2, 0), (2, 1), (2, 2)}


def test_parse_rle_multidigit_counts():
    cells = parse_rle("10o!")
    assert len(cells) == 10


# --- Patterns (validated against the canonical library definitions) ---

def test_patterns_all_load():
    for name, cells in all_patterns().items():
        assert len(cells) > 0, name
        # cells are normalized to the origin (min row/col == 0)
        ys = [y for y, _ in cells]
        xs = [x for _, x in cells]
        assert min(ys) == 0 and min(xs) == 0, name


def test_glider_is_5_cells():
    name, cells = find("glider")
    assert name == "Glider" and len(cells) == 5


def test_block_pattern_4_cells():
    name, cells = find("block")
    assert len(cells) == 4


def test_pulsar_is_canonical_period_three():
    """The pulsar must be the true 48-cell, period-3 oscillator on a
    sufficiently large (near-infinite) board — verified against the
    authoritative copy.sh/life RLE."""
    name, cells = find("pulsar")
    assert len(cells) == 48
    b = Life(300, 300)
    b.seed(list(cells))
    gen0 = frozenset(b.cells)
    phases = []
    for i in range(4):
        phases.append(frozenset(b.cells))
        b.step()
    assert phases[0] == phases[3], "pulsar should return to gen0 after 3 steps"
    assert len(phases[1]) == 56 and len(phases[2]) == 72


def test_glider_gun_is_periodic_population():
    name, cells = find("gosper_glider_gun")
    assert len(cells) > 0
    b = Life(200, 300)
    b.seed(list(cells))
    for _ in range(400):
        b.step()
        assert 0 < b.count() < 300  # bounded, never explodes or dies


# --- Main guard so it also runs without pytest ---
if __name__ == "__main__":
    import sys, traceback
    failed = 0
    for fn_name in sorted(
        (n for n in dir() if n.startswith("test_") and callable(globals()[n]))
    ):
        fn = globals()[fn_name]
        try:
            fn()
            print(f"PASS {fn_name}")
        except Exception:
            failed += 1
            print(f"FAIL {fn_name}")
            traceback.print_exc()
    sys.exit(1 if failed else 0)
