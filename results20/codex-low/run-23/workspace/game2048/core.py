"""Pure-logic 2048 game engine (no dependencies, no I/O)."""
import random


SIZE = 4


class Game:
    """A 2048 board with standard move/slide semantics.

    The board is a list of ``SIZE`` rows, each a list of ``SIZE`` integers.
    A tile of 0 represents an empty cell.
    """

    def __init__(self, rng=None):
        self.rng = rng or random.Random()
        self.board = [[0] * SIZE for _ in range(SIZE)]
        self.score = 0
        self._spawn_tile()
        self._spawn_tile()

    # -- board helpers -----------------------------------------------------

    def _empty_cells(self):
        return [
            (row, col)
            for row in range(SIZE)
            for col in range(SIZE)
            if self.board[row][col] == 0
        ]

    def _spawn_tile(self):
        empty = self._empty_cells()
        if not empty:
            return
        row, col = self.rng.choice(empty)
        self.board[row][col] = 4 if self.rng.random() < 0.1 else 2

    def can_move(self):
        if self._empty_cells():
            return True
        for row in range(SIZE):
            for col in range(SIZE):
                value = self.board[row][col]
                if col + 1 < SIZE and self.board[row][col + 1] == value:
                    return True
                if row + 1 < SIZE and self.board[row + 1][col] == value:
                    return True
        return False

    def is_game_over(self):
        return not self.can_move()

    def has_won(self, target=2048):
        return any(
            self.board[row][col] >= target
            for row in range(SIZE)
            for col in range(SIZE)
        )

    # -- moves -------------------------------------------------------------

    def _move_left(self, row):
        """Slide a single row to the left, merging equal neighbors once."""
        tiles = [value for value in row if value != 0]
        merged, gain = [], 0
        i = 0
        while i < len(tiles):
            if i + 1 < len(tiles) and tiles[i] == tiles[i + 1]:
                value = tiles[i] * 2
                merged.append(value)
                gain += value
                i += 2
            else:
                merged.append(tiles[i])
                i += 1
        merged += [0] * (SIZE - len(merged))
        return merged, gain

    def move(self, direction):
        """Apply ``direction`` in {up, down, left, right}.

        Each move reads the affected lane (row or column) out of the board,
        slides/merges it toward the edge, and writes it back. Returns ``True``
        if the board changed and a new tile was spawned.
        """
        d = direction.lower()
        if d not in ("left", "right", "up", "down"):
            raise ValueError(f"unknown direction: {direction!r}")

        # Cells of each lane, listed from the move edge inward, so sliding
        # "toward the edge" always means collapsing toward index 0.
        if d == "left":
            lanes = [[(r, c) for c in range(SIZE)] for r in range(SIZE)]
        elif d == "right":
            lanes = [[(r, c) for c in range(SIZE - 1, -1, -1)] for r in range(SIZE)]
        elif d == "up":
            lanes = [[(r, c) for r in range(SIZE)] for c in range(SIZE)]
        else:  # down
            lanes = [[(r, c) for r in range(SIZE - 1, -1, -1)] for c in range(SIZE)]

        new_board = [list(row) for row in self.board]
        gain = 0
        for lane in lanes:
            tiles = [new_board[r][c] for r, c in lane]
            tiles = [value for value in tiles if value != 0]
            merged = []
            i = 0
            while i < len(tiles):
                if i + 1 < len(tiles) and tiles[i] == tiles[i + 1]:
                    value = tiles[i] * 2
                    merged.append(value)
                    gain += value
                    i += 2
                else:
                    merged.append(tiles[i])
                    i += 1
            merged += [0] * (SIZE - len(merged))
            for (r, c), value in zip(lane, merged):
                new_board[r][c] = value

        self.score += gain
        changed = new_board != self.board
        if changed:
            self.board = new_board
            self._spawn_tile()
        return changed

    def clone(self):
        """Return an independent copy (used mostly by tests)."""
        copy = Game.__new__(Game)
        copy.rng = self.rng
        copy.board = [list(row) for row in self.board]
        copy.score = self.score
        return copy

    def __repr__(self):
        width = max(len(str(value)) for row in self.board for value in row) or 1
        lines = []
        for row in self.board:
            lines.append(" | ".join(f"{value:>{width}}" if value else "." for value in row))
        return "\n".join(lines)
