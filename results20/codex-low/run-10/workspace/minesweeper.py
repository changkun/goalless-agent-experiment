#!/usr/bin/env python3
"""Terminal Minesweeper — playable, colorful, and self-contained.

Usage:
    python3 minesweeper.py [rows cols mines]
    defaults: 9 9 10

Controls:
    arrow keys / WASD / vi-keys  : move cursor
    Z / Space / Enter            : reveal cell
    X / F                        : toggle flag
    R                            : restart
    Q                            : quit
"""
import os
import random
import sys
from dataclasses import dataclass, field


# --------------------------------------------------------------------------
# Color / style helpers (safe fallback on plain terminals)
# --------------------------------------------------------------------------
class C:
    RESET = "\x1b[0m"
    BOLD = "\x1b[1m"
    DIM = "\x1b[2m"
    REV = "\x1b[7m"
    MINE = "\x1b[31;1m"     # red bold
    FLAG = "\x1b[33;1m"     # yellow bold
    HIDDEN = "\x1b[90m"     # bright black
    OPEN = "\x1b[97m"       # bright white
    TITLE = "\x1b[96;1m"    # cyan bold
    STATUS = "\x1b[92m"     # green

    NUM = {
        1: "\x1b[34;1m", 2: "\x1b[32;1m", 3: "\x1b[31;1m",
        4: "\x1b[35;1m", 5: "\x1b[33;1m", 6: "\x1b[36;1m",
        7: "\x1b[37;1m", 8: "\x1b[33;1m",
    }


def style(text, *codes):
    return "".join(codes) + text + C.RESET


# --------------------------------------------------------------------------
# Terminal input (raw mode)
# --------------------------------------------------------------------------
def get_key():
    """Return a logical key name from raw-mode stdin."""
    ch = os.read(sys.stdin.fileno(), 1)
    if ch == b"\x1b":                      # escape sequence (arrow keys)
        seq = os.read(sys.stdin.fileno(), 2)
        return {b"[A": "up", b"[B": "down",
                b"[C": "right", b"[D": "left"}.get(seq, "q")
    if ch in (b" ", b"\n", b"\r"):
        return "z"
    if not ch:
        return "q"
    k = ch.decode("utf-8", "ignore").lower()
    return {
        "w": "up", "a": "left", "s": "down", "d": "right",
        "k": "up", "h": "left", "j": "down", "l": "right",
        "z": "z", "x": "f", "f": "f", "r": "r", "q": "q",
    }.get(k, "q")


# --------------------------------------------------------------------------
# Game state
# --------------------------------------------------------------------------
@dataclass
class Game:
    rows: int
    cols: int
    mines: int
    board: list = field(default_factory=list)       # 0..8 counts, -1 = mine
    visible: list = field(default_factory=list)     # revealed cells
    flagged: list = field(default_factory=list)     # flagged cells
    cursor: tuple = (0, 0)
    started: bool = False
    game_over: bool = False
    won: bool = False

    def __post_init__(self):
        self.board = [[0] * self.cols for _ in range(self.rows)]
        self.visible = [[False] * self.cols for _ in range(self.rows)]
        self.flagged = [[False] * self.cols for _ in range(self.rows)]

    @property
    def flags_left(self):
        return self.mines - sum(sum(row) for row in self.flagged)

    def _neighbors(self, r, c):
        for dr in (-1, 0, 1):
            for dc in (-1, 0, 1):
                if dr == 0 and dc == 0:
                    continue
                nr, nc = r + dr, c + dc
                if 0 <= nr < self.rows and 0 <= nc < self.cols:
                    yield nr, nc

    def place_mines(self, safe_r, safe_c):
        safe = {(safe_r, safe_c)} | set(self._neighbors(safe_r, safe_c))
        positions = [(r, c) for r in range(self.rows) for c in range(self.cols)
                     if (r, c) not in safe]
        random.shuffle(positions)
        for r, c in positions[:self.mines]:
            self.board[r][c] = -1
        for r in range(self.rows):
            for c in range(self.cols):
                if self.board[r][c] == -1:
                    continue
                self.board[r][c] = sum(
                    1 for nr, nc in self._neighbors(r, c)
                    if self.board[nr][nc] == -1)

    def reveal(self, r, c):
        if self.game_over or self.won or self.flagged[r][c]:
            return
        if not self.started:
            self.place_mines(r, c)
            self.started = True
        if self.board[r][c] == -1:
            self.game_over = True
            return

        stack = [(r, c)]
        while stack:
            cr, cc = stack.pop()
            if self.visible[cr][cc] or self.board[cr][cc] == -1:
                continue
            self.visible[cr][cc] = True
            if self.board[cr][cc] == 0:
                for nr, nc in self._neighbors(cr, cc):
                    if not self.visible[nr][nc] and not self.flagged[nr][nc] \
                            and self.board[nr][nc] != -1:
                        stack.append((nr, nc))

        if sum(sum(row) for row in self.visible) == self.rows * self.cols - self.mines:
            self.won = True

    def toggle_flag(self, r, c):
        if self.game_over or self.won or self.visible[r][c]:
            return
        self.flagged[r][c] = not self.flagged[r][c]


# --------------------------------------------------------------------------
# Rendering
# --------------------------------------------------------------------------
class Renderer:
    def __init__(self, game):
        self.game = game

    def _cell(self, r, c):
        g = self.game
        is_cursor = (r, c) == g.cursor

        if g.flagged[r][c]:
            body, code = "F", C.FLAG
        elif g.visible[r][c]:
            if g.board[r][c] == -1:
                body, code = "X", C.MINE
            elif g.board[r][c] == 0:
                body, code = " ", C.OPEN
            else:
                n = g.board[r][c]
                body, code = str(n), C.NUM.get(n, C.OPEN)
        elif g.game_over and g.board[r][c] == -1:
            body, code = "*", C.MINE     # show unhit mines after a loss
        else:
            body, code = " ", C.HIDDEN

        if is_cursor:
            return style(" " + body + " ", C.REV, code)
        return style(" " + body + " ", code)

    def render(self):
        g = self.game
        header = style(" MINESWEEPER ", C.BOLD, C.TITLE)
        info = style(f"{g.rows}x{g.cols}  ·  {g.mines} mines  ·  {g.flags_left} flags",
                     C.STATUS)
        controls = style("move WASD/arrows  ·  reveal Z/space  ·  flag X/F  ·  "
                         "restart R  ·  quit Q", C.DIM)
        lines = [f"{header}{info}", controls, ""]

        lines.append("     " + "".join(style(f" {chr(65 + c)} ", C.DIM)
                                       for c in range(g.cols)))
        for r in range(g.rows):
            label = style(f"{r + 1:>2}  ", C.DIM)
            row = "".join(self._cell(r, c) for c in range(g.cols))
            lines.append(label + row)

        if g.game_over:
            lines.append("")
            lines.append(style("  BOOM! You hit a mine.", C.BOLD, C.MINE))
        elif g.won:
            lines.append("")
            lines.append(style("  Congratulations, you cleared the field!", C.BOLD, C.STATUS))
        else:
            lines.append("")
            lines.append(style("  Reveal all non-mine cells to win.", C.DIM))
        return "\n".join(lines)


# --------------------------------------------------------------------------
# Main loop
# --------------------------------------------------------------------------
def play(rows, cols, mines):
    game = Game(rows, cols, mines)
    renderer = Renderer(game)
    fd = sys.stdin.fileno()

    import termios
    import tty
    old = termios.tcgetattr(fd)
    tty.setraw(fd)

    def draw():
        os.system("clear")
        print("\x1b[?25l", end="", flush=True)
        print(renderer.render(), flush=True)

    try:
        draw()
        while True:
            key = get_key()

            if game.won or game.game_over:
                if key == "r":
                    game = Game(rows, cols, mines)
                    renderer = Renderer(game)
                    draw()
                elif key == "q":
                    break
                continue

            r, c = game.cursor
            if key == "up" and r > 0:
                game.cursor = (r - 1, c)
            elif key == "down" and r < rows - 1:
                game.cursor = (r + 1, c)
            elif key == "left" and c > 0:
                game.cursor = (r, c - 1)
            elif key == "right" and c < cols - 1:
                game.cursor = (r, c + 1)
            elif key == "z":
                game.reveal(r, c)
            elif key == "f":
                game.toggle_flag(r, c)
            elif key == "r":
                game = Game(rows, cols, mines)
                renderer = Renderer(game)
            elif key == "q":
                break

            draw()
    except (KeyboardInterrupt, EOFError):
        pass
    finally:
        import termios
        try:
            termios.tcsetattr(fd, termios.TCSADRAIN, old)
        except OSError:
            pass
        os.system("clear")
        print("\x1b[?25h\x1b[0m", end="")   # restore cursor & styles


def main():
    args = sys.argv[1:]
    rows, cols, mines = 9, 9, 10
    if len(args) >= 2:
        rows, cols = int(args[0]), int(args[1])
    if len(args) >= 3:
        mines = int(args[2])
    if rows < 3 or cols < 3 or mines < 1 or mines >= rows * cols:
        sys.stderr.write("error: use a board at least 3x3 with 1..(cells-1) mines\n")
        sys.exit(1)
    play(rows, cols, mines)


if __name__ == "__main__":
    main()
