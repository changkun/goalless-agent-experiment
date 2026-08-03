"""Tests for the Game of Life engine (run with `python -m game_of_life.__tests__`)."""

from __future__ import annotations

from .engine import Life
from .patterns import BLINKER, BLOCK, GLIDER


def _assert(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def test_block_is_still_life() -> None:
    life = Life(6, 6, BLOCK)
    for _ in range(5):
        life.step()
    _assert(life.live_cells == set(BLOCK), "block should be a still life")


def test_blinker_oscillates() -> None:
    life = Life(6, 6, BLINKER)
    life.step()
    _assert(life.live_cells == {(0, 2), (1, 2), (2, 2)}, "blinker should be vertical after one step")
    life.step()
    _assert(life.live_cells == set(BLINKER), "blinker should return to horizontal")


def test_glider_moves() -> None:
    life = Life(12, 12, GLIDER)
    life.step()
    _assert(life.live_cells == {(2, 1), (2, 3), (3, 2), (3, 3), (4, 2)},
            f"glider phase after one step, got {sorted(life.live_cells)}")


def test_underpopulation_and_overpopulation() -> None:
    lonely = Life(6, 6, [(0, 0)])
    lonely.step()
    _assert(lonely.population() == 0, "lonely cell should die")

    crowded = Life(6, 6, [(1, 1), (1, 2), (1, 3), (2, 1), (2, 2), (2, 3)])
    crowded.step()
    _assert(crowded.population() == 6, "3x2 block should survive as two blocks")


def test_toroidal_wrap() -> None:
    # (4, 0) is only adjacent to (0, 0) via the top-edge wrap; together with
    # two other neighbours it should keep (0, 0) alive across the boundary.
    life = Life(5, 5, [(0, 1), (1, 0), (4, 0)])
    life.step()
    _assert((0, 0) in life.live_cells,
            f"neighbourhood should wrap around the edges, got {sorted(life.live_cells)}")


def test_invalid_dimensions() -> None:
    try:
        Life(0, 5)
    except ValueError:
        return
    raise AssertionError("zero width should raise ValueError")


_TESTS = [
    test_block_is_still_life,
    test_blinker_oscillates,
    test_glider_moves,
    test_underpopulation_and_overpopulation,
    test_toroidal_wrap,
    test_invalid_dimensions,
]


def main() -> int:
    failures = 0
    for test in _TESTS:
        try:
            test()
        except AssertionError as exc:
            failures += 1
            print(f"FAIL  {test.__name__}: {exc}")
        else:
            print(f"PASS  {test.__name__}")
    print(f"\n{len(_TESTS) - failures}/{len(_TESTS)} tests passed")
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
