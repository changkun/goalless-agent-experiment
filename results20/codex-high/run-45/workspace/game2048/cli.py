"""Terminal user interface for the 2048 game."""

from __future__ import annotations

import os
import sys
from typing import Optional

from game2048 import Game, WINNING_TILE

# ANSI color codes for tile values. Empty cells get a dim background.
_TILE_COLORS = {
    0: "\033[48;5;235m\033[38;5;245m",
    2: "\033[48;5;236m\033[38;5;252m",
    4: "\033[48;5;238m\033[38;5;252m",
    8: "\033[48;5;172m\033[38;5;16m",
    16: "\033[48;5;208m\033[38;5;16m",
    32: "\033[48;5;203m\033[38;5;16m",
    64: "\033[48;5;196m\033[38;5;255m",
    128: "\033[48;5;226m\033[38;5;16m",
    256: "\033[48;5;220m\033[38;5;16m",
    512: "\033[48;5;214m\033[38;5;16m",
    1024: "\033[48;5;209m\033[38;5;16m",
    2048: "\033[48;5;33m\033[38;5;255m",
    4096: "\033[48;5;27m\033[38;5;255m",
    8192: "\033[48;5;21m\033[38;5;255m",
}
_RESET = "\033[0m"

# Human-readable keys mapped to directions.
_KEYS = {
    "w": "up", "k": "up", "\x1b[A": "up",
    "s": "down", "j": "down", "\x1b[B": "down",
    "a": "left", "h": "left", "\x1b[D": "left",
    "d": "right", "l": "right", "\x1b[C": "right",
    "q": "quit", "\x03": "quit",
}

_HEADER = "  {title}   score: {score}   best: {best}"


def _cell(value: int, width: int) -> str:
    """Render a single cell as a centered, colored, fixed-width string."""
    color = _TILE_COLORS.get(value, _TILE_COLORS[8192])
    text = str(value) if value else ""
    return color + text.center(width) + _RESET


def _read_key() -> str:
    """Read a single keypress, decoding arrow-key escape sequences."""
    char = sys.stdin.read(1)
    if char == "\x1b":
        seq = sys.stdin.read(2)
        if seq in (("[A", "[B", "[C", "[D")):
            return "\x1b" + seq
        return char
    return char


def _setup_terminal() -> None:
    """Switch the terminal into raw mode so keys read without Enter."""
    import termios
    import tty

    fd = sys.stdin.fileno()
    old = termios.tcgetattr(fd)
    tty.setraw(fd)
    return old


def _restore_terminal(old) -> None:
    """Restore terminal settings captured by :func:`_setup_terminal`."""
    import termios

    fd = sys.stdin.fileno()
    termios.tcsetattr(fd, termios.TCSADRAIN, old)


def run(keep_playing_after_win: bool = True) -> None:
    """Play an interactive 2048 game in the terminal.

    Controls: arrows or WASD/HJKL to move, ``q`` or Ctrl-C to quit.
    """
    game = Game()
    best = 0

    # Try to enable raw mode; fall back to Enter-per-move when unsupported.
    raw = None
    try:
        if sys.stdin.isatty() and os.name != "nt":
            raw = _setup_terminal()
    except Exception:
        raw = None

    try:
        while True:
            os.system("clear" if os.name != "nt" else "cls")
            print(_HEADER.format(title="2048", score=game.score, best=best))
            print()
            print(render(board=game.board))
            print()
            print("  moves: 'wasd' / arrows   quit: 'q'")

            if game.won:
                print("\n  You reached 2048! Keep going for a higher score.")
                if not keep_playing_after_win:
                    break

            if game.over:
                print("\n  Game over!  Final score: {}".format(game.score))
                if best < game.score:
                    best = game.score
                print("  Press any key to exit.")
                if raw is not None:
                    _read_key()
                break

            key = _read_key()
            action = _KEYS.get(key)
            if action == "quit":
                break
            if action:
                game.play(action)
                if best < game.score:
                    best = game.score
    finally:
        if raw is not None:
            _restore_terminal(raw)


def render(board, width: int = 5, gap: int = 1) -> str:
    """Render a board as a colored string grid."""
    size = len(board)
    cell = " " * gap + "{cell}"
    lines: list[str] = []
    for row in board:
        cells = [cell.format(cell=_cell(v, width)) for v in row]
        lines.append((" " * gap).join(cells))
    return ("\n").join(lines)


def main() -> None:
    try:
        run()
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()
