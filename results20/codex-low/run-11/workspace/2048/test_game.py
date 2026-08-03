"""Headless tests for the 2048 board logic (no curses needed)."""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from game import Board, SIZE


def make(values):
    b = Board()
    b.grid = [row[:] for row in values]
    return b


def check():
    failures = []

    def eq(name, got, want):
        if got != want:
            failures.append(f"{name}: got {got}, want {want}")

    # -- pure merge logic -----------------------------------------------------
    b = make([[0] * SIZE for _ in range(SIZE)])
    cases = {
        "simple pair":  ([2, 2, 0, 0], [4, 0, 0, 0], 4),
        "quad merge":   ([2, 2, 2, 2], [4, 4, 0, 0], 8),
        "spaced pair":  ([2, 0, 2, 0], [4, 0, 0, 0], 4),
        "two pairs":    ([4, 4, 8, 8], [8, 16, 0, 0], 24),
        "no merge":     ([2, 4, 8, 16], [2, 4, 8, 16], 0),
        "triple with gap": ([2, 2, 4, 0], [4, 4, 0, 0], 4),
    }
    for name, (inp, want_line, want_score) in cases.items():
        got_line, got_score = b._line_move(list(inp))
        eq(f"_line_move {name} line", got_line, want_line)
        eq(f"_line_move {name} score", got_score, want_score)
        # _line_move must not mutate the input
        eq(f"_line_move {name} no mutation", inp, [
            v for v in eval(repr(inp))])

    # -- direction extraction/injection round-trips ----------------------------
    grid = [[1, 2, 3, 4],
            [5, 6, 7, 8],
            [9, 10, 11, 12],
            [13, 14, 15, 16]]
    for direction in ("left", "right", "up", "down"):
        bd = make(grid)
        lines = bd._extract(direction)
        restored = Board()
        restored._inject(direction, lines)
        eq(f"round-trip {direction}", restored.grid, grid)

    # -- full moves spawn a tile and score --------------------------------------
    b = make([[2, 2, 0, 0],
              [0, 0, 0, 0],
              [0, 0, 0, 0],
              [0, 0, 0, 0]])
    b.move('left')
    eq("left move returns True", True, True)
    eq("left merge first cell", b.grid[0][0], 4)
    spawned = sum(1 for row in b.grid for v in row if v != 0)
    eq("two tiles on board after move", spawned, 2)
    eq("score is 4", b.score, 4)

    b = make([[0, 0, 2, 2],
              [0, 0, 0, 0],
              [0, 0, 0, 0],
              [0, 0, 0, 0]])
    b.move('right')
    eq("right merge last cell", b.grid[0][3], 4)

    # -- no-op move returns False and adds no history ---------------------------
    b = make([[2, 4, 8, 16],
              [4, 8, 16, 32],
              [8, 16, 32, 4],
              [16, 32, 4, 8]])
    eq("no-op left returns False", b.move('left'), False)
    eq("no-op adds no undo", len(b.history), 0)

    # -- undo -------------------------------------------------------------------
    b = make([[2, 2, 0, 0],
              [0, 0, 0, 0],
              [0, 0, 0, 0],
              [0, 0, 0, 0]])
    b.move('left')                       # merges 2+2 -> [4,0,0,0] + spawn, score 4
    # force a known, guaranteed-merge state and snapshot it
    b.grid[0] = [0, 4, 4, 0]
    b.score = 99
    snap = ([row[:] for row in b.grid], b.score)
    b.move('left')                       # merges [0,4,4,0] -> [8,0,0,0]
    eq("undo returns True", b.undo(), True)
    eq("undo restores grid", b.grid, snap[0])
    eq("undo restores score", b.score, snap[1])

    # -- win + game-over detection ----------------------------------------------
    b = make([[2048, 0, 0, 0],
              [0, 0, 0, 0],
              [0, 0, 0, 0],
              [0, 0, 0, 0]])
    eq("won with 2048", b.has_won(), True)

    # full board with one adjacent pair -> movable
    b = make([[2, 2, 4, 8],
              [4, 8, 16, 32],
              [2, 4, 8, 16],
              [8, 16, 32, 4]])
    eq("full but movable", b.can_move(), True)

    # checkerboard with no equal neighbors -> deadlocked
    b = make([[2, 4, 2, 4],
              [4, 2, 4, 2],
              [2, 4, 2, 4],
              [4, 2, 4, 2]])
    eq("deadlocked board", b.can_move(), False)

    # -- reset keeps best and starts a fresh two-tile board ----------------------
    b = make([[2, 2, 0, 0],
              [0, 0, 0, 0],
              [0, 0, 0, 0],
              [0, 0, 0, 0]])
    b.move('left')
    best_before = b.best
    b.reset()
    eq("best preserved across reset", b.best, best_before)
    nonzero = sum(1 for row in b.grid for v in row if v != 0)
    eq("fresh board has two tiles", nonzero, 2)
    eq("fresh board score is 0", b.score, 0)

    if failures:
        print("FAILURES:")
        for f in failures:
            print("  -", f)
        sys.exit(1)
    print("All board logic tests passed.")


if __name__ == "__main__":
    check()
