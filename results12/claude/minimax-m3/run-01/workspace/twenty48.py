"""2048 — terminal edition.

Pure stdlib, no dependencies. The game logic is decoupled from the UI so it
can be exercised without a TTY (see ``if __name__ == "__main__"``).
"""

from __future__ import annotations

import argparse
import copy
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Iterable, List, Optional, Sequence, Tuple


SIZE = 4
TARGET = 2048

# ANSI colors for each power-of-two tile value. 0 = empty cell.
# Picked to match the well-known 2048 palette; fall back to plain for non-TTYs.
TILE_COLORS = {
    0:    ("\033[90m",  "\033[100m"),  # empty: grey on dark grey
    2:    ("\033[30m",  "\033[107m"),  # black on near-white
    4:    ("\033[30m",  "\033[47m"),
    8:    ("\033[97m",  "\033[43m"),   # white on yellow
    16:   ("\033[97m",  "\033[101m"),
    32:   ("\033[97m",  "\033[41m"),
    64:   ("\033[97m",  "\033[33;1;7m"),
    128:  ("\033[30m",  "\033[106m"),
    256:  ("\033[30m",  "\033[102m"),
    512:  ("\033[97m",  "\033[35m"),
    1024: ("\033[97m",  "\033[44m"),
    2048: ("\033[97m",  "\033[42m"),
    4096: ("\033[30m",  "\033[46m"),
    8192: ("\033[97m",  "\033[45m"),
}
RESET = "\033[0m"
BOLD = "\033[1m"
DIM = "\033[2m"
CLEAR = "\033[2J\033[H"


# ---------- Core game logic ---------- #

@dataclass
class Game:
    board: List[List[int]] = field(default_factory=lambda: [[0] * SIZE for _ in range(SIZE)])
    score: int = 0
    moves: int = 0
    won: bool = False
    over: bool = False
    rng: random.Random = field(default_factory=random.Random)

    def reset(self) -> None:
        self.board = [[0] * SIZE for _ in range(SIZE)]
        self.score = 0
        self.moves = 0
        self.won = False
        self.over = False
        for _ in range(2):
            self._spawn()

    def empty_cells(self) -> List[Tuple[int, int]]:
        return [(r, c) for r in range(SIZE) for c in range(SIZE) if self.board[r][c] == 0]

    def _spawn(self) -> Optional[Tuple[int, int, int]]:
        empties = self.empty_cells()
        if not empties:
            return None
        r, c = self.rng.choice(empties)
        # 90% a 2, 10% a 4 — matches the original.
        value = 4 if self.rng.random() < 0.1 else 2
        self.board[r][c] = value
        return r, c, value

    def spawn(self) -> None:
        # Public spawn for tests / hot-restart paths.
        self._spawn()

    @staticmethod
    def _slide_row_left(row: Sequence[int]) -> Tuple[List[int], int, bool]:
        """Slide one row to the left. Returns (new_row, score_gained, merged)."""
        gained = 0
        merged = False
        # Strip zeros.
        tiles = [v for v in row if v != 0]
        out: List[int] = []
        i = 0
        while i < len(tiles):
            if i + 1 < len(tiles) and tiles[i] == tiles[i + 1]:
                merged_val = tiles[i] * 2
                out.append(merged_val)
                gained += merged_val
                merged = True
                i += 2
            else:
                out.append(tiles[i])
                i += 1
        out.extend([0] * (SIZE - len(out)))
        return out, gained, merged

    def move(self, direction: str) -> bool:
        """Apply a move. direction is one of 'up', 'down', 'left', 'right'.
        Returns True if the board changed (i.e. the move was legal)."""
        if self.over:
            return False
        before = [row[:] for row in self.board]
        gained = 0

        if direction in ("left", "right"):
            for r in range(SIZE):
                row = self.board[r]
                if direction == "right":
                    row = list(reversed(row))
                new_row, g, _ = self._slide_row_left(row)
                if direction == "right":
                    new_row = list(reversed(new_row))
                self.board[r] = new_row
                gained += g
        elif direction in ("up", "down"):
            for c in range(SIZE):
                col = [self.board[r][c] for r in range(SIZE)]
                if direction == "down":
                    col = list(reversed(col))
                new_col, g, _ = self._slide_row_left(col)
                if direction == "down":
                    new_col = list(reversed(new_col))
                for r in range(SIZE):
                    self.board[r][c] = new_col[r]
                gained += g
        else:
            raise ValueError(f"unknown direction: {direction}")

        if self.board == before:
            return False

        self.score += gained
        self.moves += 1
        self._spawn()
        if not self._has_moves():
            self.over = True
        return True

    def _has_moves(self) -> bool:
        if self.empty_cells():
            return True
        for r in range(SIZE):
            for c in range(SIZE):
                v = self.board[r][c]
                if r + 1 < SIZE and self.board[r + 1][c] == v:
                    return True
                if c + 1 < SIZE and self.board[r][c + 1] == v:
                    return True
        return False

    def check_won(self) -> bool:
        if not self.won and TARGET in (v for row in self.board for v in row):
            self.won = True
        return self.won


# ---------- Rendering ---------- #

def _supports_color() -> bool:
    if os.environ.get("NO_COLOR") is not None:
        return False
    if not sys.stdout.isatty():
        return False
    return True


def render(game: Game, *, color: bool = True) -> str:
    c = color and _supports_color()
    out: List[str] = []

    def tile_str(value: int) -> str:
        text = "." if value == 0 else str(value)
        if not c:
            return text.rjust(4)
        fg, bg = TILE_COLORS.get(value, ("\033[97m", "\033[45m"))
        return f"{bg}{fg}{BOLD} {text:^4} {RESET}"

    out.append(f"{BOLD}2048{RESET}    "
               f"score {DIM}{game.score}{RESET}    "
               f"moves {DIM}{game.moves}{RESET}" if c else
               f"2048    score {game.score}    moves {game.moves}")
    out.append("")

    width = 4 * 5 + 1  # each cell is 5 chars including border
    sep = "+" + ("-" * 5 + "+") * SIZE
    out.append(sep)
    for r in range(SIZE):
        row_str = "|" + "|".join(tile_str(v) for v in game.board[r]) + "|"
        out.append(row_str)
        out.append(sep)

    if game.won and not game.over:
        out.append("")
        out.append(f"{BOLD}You reached 2048! Keep going or press 'r' to restart.{RESET}"
                   if c else "You reached 2048! Keep going or press 'r' to restart.")
    if game.over:
        out.append("")
        out.append(f"{BOLD}Game over.{RESET} press 'r' to play again, 'q' to quit."
                   if c else "Game over. press 'r' to play again, 'q' to quit.")
    return "\n".join(out)


# ---------- Input ---------- #

KEY_TO_DIR = {
    "h": "left",  "left":  "left",  "\x1b[D": "left",
    "l": "right", "right": "right", "\x1b[C": "right",
    "k": "up",    "up":    "up",    "\x1b[A": "up",
    "j": "down",  "down":  "down",  "\x1b[B": "down",
    "a": "left",  "d": "right", "w": "up", "s": "down",
}


def _read_key() -> str:
    """Read a single keypress (with arrow-key escape parsing). Falls back
    to normal input() when stdin is not a TTY."""
    if not sys.stdin.isatty():
        return sys.stdin.readline().strip().lower()

    try:
        import termios
        import tty
    except ImportError:  # non-POSIX (shouldn't happen on Linux, but be safe)
        return input().strip().lower()

    fd = sys.stdin.fileno()
    old = termios.tcgetattr(fd)
    try:
        tty.setraw(fd)
        ch1 = os.read(fd, 1).decode("utf-8", errors="ignore")
        if ch1 == "\x1b":
            # Arrow keys are ESC [ A/B/C/D — read the rest if it shows up.
            ch2 = os.read(fd, 1).decode("utf-8", errors="ignore")
            if ch2 == "[":
                ch3 = os.read(fd, 1).decode("utf-8", errors="ignore")
                return ch1 + ch2 + ch3
            return ch1 + ch2
        return ch1
    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, old)


# ---------- Main loop ---------- #

def play(seed: Optional[int] = None, ai: bool = False) -> int:
    game = Game(rng=random.Random(seed) if seed is not None else Game().rng)
    game.reset()

    if sys.stdout.isatty():
        sys.stdout.write(CLEAR)
    sys.stdout.write(render(game) + "\n")
    sys.stdout.flush()

    while True:
        if ai:
            direction = _greedy_ai_move(game)
            if direction is None:
                sys.stdout.write("\n[ai] no legal moves — game over.\n")
                return 0
            import time as _t
            _t.sleep(0.05)
        else:
            key = _read_key().lower()
            if key in ("q", "quit", "\x03", "\x04"):
                sys.stdout.write("\nbye.\n")
                return 0
            if key in ("r", "reset"):
                game.reset()
                if sys.stdout.isatty():
                    sys.stdout.write(CLEAR)
                sys.stdout.write(render(game) + "\n")
                sys.stdout.flush()
                continue
            direction = KEY_TO_DIR.get(key)
            if direction is None:
                continue

        moved = game.move(direction)
        game.check_won()
        if sys.stdout.isatty():
            sys.stdout.write(CLEAR)
        sys.stdout.write(render(game) + "\n")
        if not moved and not ai:
            if _supports_color():
                sys.stdout.write(f"{DIM}(no tiles moved — try a different direction){RESET}\n")
            else:
                sys.stdout.write("(no tiles moved — try a different direction)\n")
        sys.stdout.flush()

        if game.over and ai:
            sys.stdout.write(f"\n[ai] final score: {game.score} in {game.moves} moves.\n")
            return 0
        if game.over and not sys.stdin.isatty():
            return 0


def _greedy_ai_move(game: Game) -> Optional[str]:
    """Pick a move that maximizes the number of merges available, breaking
    ties by preferring directions that move tiles toward the bottom-left
    corner (the standard 'snake' strategy). Returns None if no move is legal.
    """
    best: Optional[Tuple[int, int, str]] = None
    # Preference order for corner strategy: down, left, up, right.
    pref = ["down", "left", "up", "right"]
    for d in ["up", "down", "left", "right"]:
        g = copy.deepcopy(game)
        if not g.move(d):
            continue
        merges = sum(1 for r in range(SIZE) for c in range(SIZE)
                     if g.board[r][c] != 0
                     and (r + 1 < SIZE and g.board[r][c] == g.board[r + 1][c]
                          or c + 1 < SIZE and g.board[r][c] == g.board[r][c + 1]))
        score = (merges, -pref.index(d))
        if best is None or score > best[:2]:
            best = (score[0], score[1], d)
    return best[2] if best else None


# ---------- Self-test (runs without a TTY) ---------- #

def _run_self_tests() -> int:
    failures: List[str] = []

    def check(name: str, cond: bool, detail: str = "") -> None:
        if not cond:
            failures.append(f"{name}: {detail}")

    # _slide_row_left: basic slide, merge, no-merge-double-merge.
    new, gained, _ = Game._slide_row_left([2, 2, 4, 4])
    check("slide merges pairs in order", new == [4, 8, 0, 0] and gained == 12,
          f"got {new}, gained {gained}")

    new, gained, _ = Game._slide_row_left([0, 2, 0, 2])
    check("slide collapses zeros", new == [4, 0, 0, 0] and gained == 4,
          f"got {new}, gained {gained}")

    new, gained, _ = Game._slide_row_left([2, 0, 0, 0])
    check("slide single tile", new == [2, 0, 0, 0] and gained == 0,
          f"got {new}, gained {gained}")

    new, gained, _ = Game._slide_row_left([2, 2, 2, 2])
    check("slide merges in pairs, not chains", new == [4, 4, 0, 0] and gained == 8,
          f"got {new}, gained {gained}")

    # Full board move.
    g = Game(rng=random.Random(0))
    g.board = [
        [2, 2, 0, 0],
        [0, 0, 0, 0],
        [0, 0, 0, 0],
        [0, 0, 0, 0],
    ]
    g._spawn = lambda: None  # type: ignore[assignment]  # don't pollute the test
    moved = g.move("left")
    check("left move changes board when tiles merge", moved and g.board[0] == [4, 0, 0, 0],
          f"board[0]={g.board[0]}")
    check("score reflects merge", g.score == 4, f"score={g.score}")
    check("moves counter increments", g.moves == 1, f"moves={g.moves}")

    # A no-op move should return False and not change the board.
    g.board = [
        [2, 4, 8, 16],
        [0, 0, 0, 0],
        [0, 0, 0, 0],
        [0, 0, 0, 0],
    ]
    g.score = 0
    g.moves = 0
    g._spawn = lambda: None  # type: ignore[assignment]
    moved = g.move("left")
    check("illegal move returns False", moved is False)
    check("illegal move does not increment score", g.score == 0)

    # Up / right / down: a small but non-trivial board.
    g.board = [
        [2, 0, 0, 0],
        [2, 0, 0, 0],
        [0, 0, 0, 0],
        [0, 0, 0, 0],
    ]
    g.score = 0
    g._spawn = lambda: None  # type: ignore[assignment]
    g.move("up")
    check("up move stacks", g.board[0][0] == 4 and g.board[1][0] == 0,
          f"col 0 = {[g.board[r][0] for r in range(SIZE)]}")

    g.board = [
        [0, 0, 2, 2],
        [0, 0, 0, 0],
        [0, 0, 0, 0],
        [0, 0, 0, 0],
    ]
    g.score = 0
    g._spawn = lambda: None  # type: ignore[assignment]
    g.move("right")
    check("right move stacks to right edge",
          g.board[0] == [0, 0, 0, 4],
          f"row 0 = {g.board[0]}")

    g.board = [
        [0, 0, 0, 0],
        [0, 0, 0, 0],
        [2, 0, 0, 0],
        [2, 0, 0, 0],
    ]
    g.score = 0
    g._spawn = lambda: None  # type: ignore[assignment]
    g.move("down")
    check("down move stacks to bottom",
          g.board[3] == [4, 0, 0, 0],
          f"row 3 = {g.board[3]}")

    # Game-over detection: a full board with no adjacent equals and no empties.
    g.board = [
        [2, 4, 2, 4],
        [4, 2, 4, 2],
        [2, 4, 2, 4],
        [4, 2, 4, 2],
    ]
    check("full board with no merges is over", g._has_moves() is False)

    g.board = [
        [2, 2, 4, 8],
        [4, 8, 2, 4],
        [2, 4, 8, 2],
        [4, 2, 4, 8],
    ]
    check("full board with horizontal pair has moves", g._has_moves() is True)

    g.board = [
        [2, 4, 2, 4],
        [4, 2, 4, 2],
        [2, 4, 2, 2],  # last row: 2,2 pair
        [4, 2, 4, 2],
    ]
    check("full board with bottom-right pair has moves", g._has_moves() is True)

    # Win detection.
    g.board = [[0] * SIZE for _ in range(SIZE)]
    g.board[0][0] = 2048
    check("check_won flips on 2048", g.check_won() is True)
    check("check_won is sticky", g.check_won() is True)
    g.board = [[0] * SIZE for _ in range(SIZE)]
    g.board[0][0] = 1024
    g.won = False
    check("no win without 2048", g.check_won() is False)

    # Spawn only ever lands on empty cells and the value is 2 or 4.
    g = Game(rng=random.Random(42))
    g.reset()
    placed = [(r, c, g.board[r][c])
              for r in range(SIZE) for c in range(SIZE)
              if g.board[r][c] != 0]
    check("reset places exactly 2 tiles", len(placed) == 2,
          f"placed={placed}")
    check("spawned tiles are 2 or 4", all(v in (2, 4) for _, _, v in placed),
          f"placed={placed}")

    if failures:
        print("FAILED:")
        for f in failures:
            print("  -", f)
        return 1
    print(f"ok — {len(failures) == 0} (all self-tests passed)")
    return 0


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="2048 in your terminal.")
    parser.add_argument("--seed", type=int, default=None,
                        help="Seed the random number generator for reproducible games.")
    parser.add_argument("--test", action="store_true",
                        help="Run the self-test suite and exit.")
    parser.add_argument("--ai", action="store_true",
                        help="Watch a simple greedy AI play the game itself.")
    ns = parser.parse_args(argv)
    if ns.test:
        return _run_self_tests()
    return play(seed=ns.seed, ai=ns.ai)


if __name__ == "__main__":
    sys.exit(main())
