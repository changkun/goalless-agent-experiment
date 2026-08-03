"""
Terminal Minesweeper - a self-contained, zero-dependency implementation.

Run with:  python3 -m minesweeper.game
"""

import random
import sys
from dataclasses import dataclass


DIFFICULTIES = {
    "beginner": {"rows": 9, "cols": 9, "mines": 10},
    "intermediate": {"rows": 16, "cols": 16, "mines": 40},
    "expert": {"rows": 16, "cols": 30, "mines": 99},
}

CELL_HIDDEN = "."
CELL_FLAG = "F"
CELL_MINE = "*"
CELL_REVEALED = " "


def cell_symbol(value, revealed):
    """Return the display character for a cell."""
    if not revealed:
        return CELL_HIDDEN
    if value == -1:
        return CELL_MINE
    return CELL_REVEALED if value == 0 else str(value)


@dataclass
class Board:
    rows: int
    cols: int
    mines: int
    grid: list  # -1 = mine, otherwise adjacent-mine count
    revealed: list  # bool per cell
    flagged: list  # bool per cell
    first_move: bool = True

    @classmethod
    def create(cls, rows, cols, mines):
        grid = [[0] * cols for _ in range(rows)]
        revealed = [[False] * cols for _ in range(rows)]
        flagged = [[False] * cols for _ in range(rows)]
        return cls(rows, cols, mines, grid, revealed, flagged)

    def _in_bounds(self, r, c):
        return 0 <= r < self.rows and 0 <= c < self.cols

    def neighbors(self, r, c):
        for dr in (-1, 0, 1):
            for dc in (-1, 0, 1):
                if dr == 0 and dc == 0:
                    continue
                nr, nc = r + dr, c + dc
                if self._in_bounds(nr, nc):
                    yield nr, nc

    def place_mines(self, safe_r, safe_c):
        """Place mines avoiding the first-clicked cell and its neighbors."""
        protected = {(safe_r, safe_c)}
        protected.update(self.neighbors(safe_r, safe_c))

        candidates = [
            (r, c)
            for r in range(self.rows)
            for c in range(self.cols)
            if (r, c) not in protected
        ]
        mine_spots = random.sample(candidates, self.mines)
        for r, c in mine_spots:
            self.grid[r][c] = -1

        # Compute adjacency counts.
        for r in range(self.rows):
            for c in range(self.cols):
                if self.grid[r][c] != -1:
                    self.grid[r][c] = sum(
                        1 for nr, nc in self.neighbors(r, c) if self.grid[nr][nc] == -1
                    )

    def reveal(self, r, c):
        """Reveal a cell. Returns False if the revealed cell is a mine (game over)."""
        if not self._in_bounds(r, c) or self.revealed[r][c] or self.flagged[r][c]:
            return True

        if self.first_move:
            self.place_mines(r, c)
            self.first_move = False

        if self.grid[r][c] == -1:
            self.revealed[r][c] = True
            return False

        self._flood_fill(r, c)
        return True

    def _flood_fill(self, r, c):
        """Recursively reveal empty regions."""
        stack = [(r, c)]
        while stack:
            cr, cc = stack.pop()
            if not self._in_bounds(cr, cc) or self.revealed[cr][cc] or self.flagged[cr][cc]:
                continue
            self.revealed[cr][cc] = True
            if self.grid[cr][cc] == 0:
                for nr, nc in self.neighbors(cr, cc):
                    if not self.revealed[nr][nc] and not self.flagged[nr][nc]:
                        stack.append((nr, nc))

    def toggle_flag(self, r, c):
        if not self._in_bounds(r, c) or self.revealed[r][c]:
            return
        self.flagged[r][c] = not self.flagged[r][c]

    def is_won(self):
        """Win when every non-mine cell is revealed."""
        total = self.rows * self.cols
        safe_cells = total - self.mines
        revealed_count = sum(sum(row) for row in self.revealed)
        return revealed_count == safe_cells

    def remaining_mines(self):
        return self.mines - sum(sum(row) for row in self.flagged)

    def render(self):
        lines = []
        header = "   " + " ".join(f"{c % 10}" for c in range(self.cols))
        lines.append(header)
        sep = "  " + "+" + "---+" * self.cols
        lines.append(sep)
        for r in range(self.rows):
            row_cells = []
            for c in range(self.cols):
                if self.flagged[r][c]:
                    row_cells.append(" F ")
                else:
                    row_cells.append(f" {cell_symbol(self.grid[r][c], self.revealed[r][c])} ")
            lines.append(f"{r % 10} |" + "|".join(row_cells) + "|")
            lines.append(sep)
        return "\n".join(lines)


def parse_coord(text, rows, cols):
    """Parse input like 'r c' -> (row, col)."""
    parts = text.lower().replace(",", " ").split()
    if len(parts) < 2:
        raise ValueError("Expected format: <row> <col>")
    r, c = int(parts[0]), int(parts[1])
    if not (0 <= r < rows and 0 <= c < cols):
        raise ValueError(f"Coordinates must be within 0..{rows - 1} and 0..{cols - 1}")
    return r, c


def choose_difficulty():
    print("Choose a difficulty:")
    for i, name in enumerate(DIFFICULTIES, start=1):
        cfg = DIFFICULTIES[name]
        print(f"  {i}) {name.capitalize():12} {cfg['rows']}x{cfg['cols']}, {cfg['mines']} mines")
    while True:
        choice = input("> ").strip().lower()
        if choice in DIFFICULTIES:
            return DIFFICULTIES[choice]
        try:
            idx = int(choice)
            if 1 <= idx <= len(DIFFICULTIES):
                return DIFFICULTIES[list(DIFFICULTIES)[idx - 1]]
        except ValueError:
            pass
        print("Invalid choice, try again.")


def reveal_all_mines(board):
    for r in range(board.rows):
        for c in range(board.cols):
            if board.grid[r][c] == -1:
                board.revealed[r][c] = True


def play(board):
    print(board.render())
    while True:
        print(f"\nMines left: {board.remaining_mines()}")
        raw = input("Enter 'r <row> <col>', 'f <row> <col>', or 'q' to quit: ").strip()
        if not raw:
            continue
        if raw.lower() == "q":
            print("Quitting. Bye!")
            return None

        tokens = raw.split()
        verb = tokens[0].lower()
        try:
            r, c = parse_coord(" ".join(tokens[1:]), board.rows, board.cols)
        except (ValueError, IndexError) as exc:
            print(f"  [bad input] {exc}")
            continue

        if verb == "f":
            board.toggle_flag(r, c)
        elif verb == "r":
            if not board.reveal(r, c):
                reveal_all_mines(board)
                print(board.render())
                print("\nBoom! You hit a mine. Game over.")
                return False
        else:
            print("  [bad input] Use 'r' (reveal) or 'f' (flag).")
            continue

        print(board.render())

        if board.is_won():
            print("\nCongratulations! You cleared the board. You win!")
            return True


def main():
    try:
        import colorama  # optional; fall back to plain if unavailable
        colorama.init()
    except ImportError:
        pass

    print("=" * 40)
    print("         MINESWEEPER")
    print("=" * 40)

    while True:
        cfg = choose_difficulty()
        board = Board.create(cfg["rows"], cfg["cols"], cfg["mines"])
        result = play(board)
        again = input("\nPlay again? (y/n): ").strip().lower()
        if again not in ("y", "yes"):
            print("Thanks for playing!")
            return 0


if __name__ == "__main__":
    sys.exit(main())
