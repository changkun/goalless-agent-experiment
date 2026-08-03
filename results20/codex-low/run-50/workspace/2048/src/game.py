"""Core logic for a 2048 clone.

Pure Python, stdlib only. The game state is a 2D ``list`` of ``int``s
where ``0`` represents an empty cell. All merging rules follow the
standard 2048 rules.
"""

import random

WIN_TILE = 2048


class GameOver(Exception):
    """Raised when no legal moves remain."""


class Game:
    """A single 2048 game session."""

    win_tile = WIN_TILE

    def __init__(self, size=4, rng=None):
        self.size = size
        self.rng = rng or random.Random()
        if self.size < 2:
            raise ValueError("size must be at least 2")
        self.board = [[0] * self.size for _ in range(self.size)]
        self.score = 0
        self.moves = 0
        self.over = False
        self.won = False
        self.spawn_tile()
        self.spawn_tile()

    # -- board helpers -------------------------------------------------

    def empty_cells(self):
        return [(r, c)
                for r in range(self.size)
                for c in range(self.size)
                if self.board[r][c] == 0]

    def spawn_tile(self):
        """Add a 2 (90%) or 4 (10%) to a random empty cell."""
        empty = self.empty_cells()
        if not empty:
            return False
        r, c = self.rng.choice(empty)
        self.board[r][c] = 2 if self.rng.random() < 0.9 else 4
        return True

    def copy(self):
        clone = Game.__new__(Game)
        clone.rng = self.rng
        clone.board = [row[:] for row in self.board]
        clone.score = self.score
        clone.moves = self.moves
        clone.over = self.over
        clone.won = self.won
        return clone

    # -- movement ------------------------------------------------------

    @staticmethod
    def _merge_line(line):
        """Merge a single row 'toward index 0' and return (merged, gained)."""
        # Drop zeros, then stack equal neighbours.
        tiles = [t for t in line if t != 0]
        merged = []
        gained = 0
        i = 0
        while i < len(tiles):
            if i + 1 < len(tiles) and tiles[i] == tiles[i + 1]:
                merged.append(tiles[i] * 2)
                gained += tiles[i] * 2
                i += 2
            else:
                merged.append(tiles[i])
                i += 1
        merged += [0] * (len(line) - len(merged))
        return merged, gained

    def _slide(self, board, direction):
        """Sliding a board modifies it in place. Returns (moved, gained)."""
        if direction not in ("left", "right", "up", "down"):
            raise ValueError(f"unknown direction: {direction!r}")
        size = self.size
        if direction == "left":
            lines = [board[r] for r in range(size)]
            loc = lambda r, i: (r, i)              # noqa: E731
        elif direction == "right":
            lines = [list(reversed(board[r])) for r in range(size)]
            loc = lambda r, i: (r, size - 1 - i)   # noqa: E731
        elif direction == "up":
            lines = [[board[r][c] for r in range(size)] for c in range(size)]
            loc = lambda c, i: (i, c)              # noqa: E731
        else:  # down
            lines = [list(reversed([board[r][c] for r in range(size)]))
                     for c in range(size)]
            loc = lambda c, i: (size - 1 - i, c)   # noqa: E731

        moved = False
        gained = 0
        for idx, line in enumerate(lines):
            merged, g = self._merge_line(line)
            gained += g
            for i, value in enumerate(merged):
                r, c = loc(idx, i)
                if board[r][c] != value:
                    moved = True
                board[r][c] = value
        return moved, gained

    def move(self, direction):
        """Perform a move. Returns True if the board changed."""
        if self.over:
            return False
        attempted = self.copy()
        moved, gained = self._slide(self.board, direction)
        if not moved:
            return False
        self.moves += 1
        self.score += gained
        if self._reached_win():
            self.won = True
        self.spawn_tile()
        if not self._has_moves():
            self.over = True
        return True

    def _reached_win(self):
        return any(tile >= self.win_tile
                   for row in self.board for tile in row)

    def _has_moves(self):
        if self.empty_cells():
            return True
        for r in range(self.size):
            for c in range(self.size):
                tile = self.board[r][c]
                if c + 1 < self.size and self.board[r][c + 1] == tile:
                    return True
                if r + 1 < self.size and self.board[r + 1][c] == tile:
                    return True
        return False

    # -- rendering -----------------------------------------------------

    def render(self):
        """Return a text representation of the board."""
        cell_w = len(str(max(self.win_tile ** 2, 4)))
        rows = []
        for row in self.board:
            cells = " | ".join(
                f"{t:>{cell_w}}" if t else " " * cell_w
                for t in row
            )
            rows.append(cells)
        border = "-" * len(rows[0])
        return "\n".join([border] + rows + [border])

    def status(self):
        if self.over:
            return "Game over"
        if self.won:
            return "You won!"
        return f"Score: {self.score}  Moves: {self.moves}"


class Direction:
    """Normalise a key name to a direction, or None."""

    MAP = {
        "w": "up", "up": "up",
        "s": "down", "down": "down",
        "a": "left", "left": "left",
        "d": "right", "right": "right",
        "k": "up", "j": "down", "h": "left", "l": "right",
    }

    @classmethod
    def resolve(cls, key):
        return cls.MAP.get(key.lower() if isinstance(key, str) else key)
