"""Tests for the Game of Life board and patterns.

Run with:  python -m pytest
"""

import pytest

from game_of_life.board import bbox, render, tick
from game_of_life.patterns import ALL_PATTERNS, patterns_at


# --------------------------------------------------------------------------
# Rules
# --------------------------------------------------------------------------

def test_blinker_oscillates():
    blinker = ALL_PATTERNS["blinker"]  # centered on origin
    assert blinker == {(-1, 0), (0, 0), (1, 0)}

    vertical = tick(blinker)
    assert vertical == {(0, -1), (0, 0), (0, 1)}

    assert tick(vertical) == blinker  # period 2


def test_block_is_still_life():
    block = ALL_PATTERNS["block"]
    assert tick(block) == block


def test_underpopulation_dies():
    # A single cell has zero neighbors -> dies.
    assert tick({(0, 0)}) == set()


def test_overpopulation_dies():
    # A 2x3 filled rectangle: the four middle cells have 4 neighbors -> die;
    # the four corners keep 3 neighbors -> survive; cells born one row above
    # and below the rectangle (3 neighbors) come alive.
    cells = {(0, 0), (1, 0), (2, 0), (0, 1), (1, 1), (2, 1)}
    result = tick(cells)
    # Corners keep 3 neighbors -> survive; middle cells are crowded -> die;
    # (1, -1) and (1, 2) are born just outside the rectangle (3 neighbors).
    assert result == {(0, 0), (2, 0), (0, 1), (2, 1), (1, -1), (1, 2)}


def test_empty_stays_empty():
    assert tick(set()) == set()


def test_glider_moves_diagonally():
    g = ALL_PATTERNS["glider"]
    after = g
    for _ in range(4):  # one full period
        after = tick(after)
    # After 4 generations the glider returns to its shape, shifted (1, 1).
    assert after == {(x + 1, y + 1) for x, y in g}


# --------------------------------------------------------------------------
# Rendering
# --------------------------------------------------------------------------

def test_bbox_of_empty_is_none():
    assert bbox(set()) is None


def test_bbox_of_block():
    assert bbox(ALL_PATTERNS["block"]) == (-1, -1, 0, 0)


def test_render_produces_expected_grid():
    cells = {(0, 0), (1, 0)}
    out = render(cells, height=2, width=4)
    assert out == "##..\n...."


def test_render_honors_origin():
    cells = {(5, 5)}
    out = render(cells, height=2, width=2, origin=(5, 5))
    assert out == "#.\n.."


def test_render_crops_cells_outside_viewport():
    cells = {(100, 100)}
    assert render(cells, height=2, width=2) == "..\n.."


# --------------------------------------------------------------------------
# Patterns
# --------------------------------------------------------------------------

def test_unknown_pattern_raises():
    with pytest.raises(ValueError):
        patterns_at({"not-a-pattern": set()})


def test_patterns_at_composes():
    combo = patterns_at({"blinker": None})
    assert combo == ALL_PATTERNS["blinker"]


def test_known_patterns_are_nonempty():
    for name, cells in ALL_PATTERNS.items():
        assert cells, name
