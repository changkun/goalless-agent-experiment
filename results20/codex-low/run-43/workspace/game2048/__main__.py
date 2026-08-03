"""Terminal UI for the 2048 game.

Play with the arrow keys or W/A/S/D. Press Q to quit, R to restart.
"""

from __future__ import annotations

import sys
import termios
import tty

from . import __version__
from .logic import (
    DOWN,
    LEFT,
    RIGHT,
    UP,
    add_random_tile,
    blank_board,
    can_move,
    has_won,
    move,
)

_COLORS = {
    0: "",
    2: "\033[38;5;250m",
    4: "\033[38;5;252m",
    8: "\033[38;5;220m",
    16: "\033[38;5;214m",
    32: "\033[38;5;208m",
    64: "\033[38;5;202m",
    128: "\033[38;5;198m",
    256: "\033[38;5;200m",
    512: "\033[38;5;141m",
    1024: "\033[38;5;99m",
    2048: "\033[38;5;93m",
}
_GOLD = "\033[38;5;226m"
_RESET = "\033[0m"
_BOLD = "\033[1m"
_DIM = "\033[2m"

SIZE = 4


def _read_single_char() -> str:
    ch = sys.stdin.read(1)
    if ch == "\x1b":
        sys.stdin.read(1)  # '['
        seq = sys.stdin.read(1)
        return {"A": "up", "B": "down", "C": "right", "D": "left"}.get(seq, "")
    return ch


def interpret(ch: str):
    return {
        "w": "up", "W": "up",
        "s": "down", "S": "down",
        "a": "left", "A": "left",
        "d": "right", "D": "right",
        "r": "restart", "R": "restart",
        "q": "quit", "Q": "quit",
        "up": "up", "down": "down", "left": "left", "right": "right",
        "\x1b": "quit",
    }.get(ch)


def color_for(value: int) -> str:
    if value >= 2048:
        return _GOLD
    return _COLORS.get(value, _GOLD)


def render(board, score: int, size: int = SIZE) -> str:
    width = max(5, len(str(max(max(row, default=0) for row in board)))) + 2
    lines = [f"{_BOLD}Score: {score}{_RESET}"]
    lines.append("-" * (width * size + size + 1))
    for row in board:
        cells = []
        for value in row:
            text = str(value) if value else ""
            cell = f"{text:^{width}}"
            if value:
                cell = color_for(value) + _BOLD + cell + _RESET
            cells.append(cell)
        lines.append("|" + "|".join(cells) + "|")
    lines.append("-" * (width * size + size + 1))
    return "\n".join(lines)


def _setup_terminal():
    if not sys.stdin.isatty():
        return None
    fd = sys.stdin.fileno()
    old = termios.tcgetattr(fd)
    tty.setraw(fd)
    return old


def _restore(old) -> None:
    if old is not None:
        termios.tcsetattr(sys.stdin.fileno(), termios.TCSADRAIN, old)


def play(seed=None) -> None:
    import random

    rng = random.Random(seed)
    board = blank_board(SIZE)
    add_random_tile(board, rng)
    add_random_tile(board, rng)
    score = 0
    won = False

    old = _setup_terminal()
    try:
        print("\033[2J\033[H", end="", flush=True)
        while True:
            print("\033[H", end="")
            print(render(board, score))
            print(f"{_DIM}Arrows/WASD move, R restart, Q quit{_RESET}")

            if has_won(board) and not won:
                won = True
                print(f"{_GOLD}{_BOLD}You reached 2048! Keep going or press Q to quit.{_RESET}")

            if not can_move(board):
                print(f"{_BOLD}Game over! Final score {score}. Press Q to quit, R to restart.{_RESET}")

            action = interpret(_read_single_char())
            if action is None:
                continue
            if action == "quit":
                print("\nBye!")
                return
            if action == "restart":
                board = blank_board(SIZE)
                add_random_tile(board, rng)
                add_random_tile(board, rng)
                score = 0
                won = False
                continue

            direction = {"left": LEFT, "right": RIGHT, "up": UP, "down": DOWN}[action]
            _, gained, moved = move(board, direction)
            if moved:
                score += gained
                add_random_tile(board, rng)
            print("\033[2J\033[H", end="", flush=True)
    finally:
        _restore(old)


def main() -> None:
    seed = None
    args = sys.argv[1:]
    if len(args) == 2 and args[0] == "--seed":
        seed = int(args[1])
    if seed is not None:
        print(f"{_DIM}2048 v{__version__} -- seeded demo{_RESET}")
    play(seed=seed)
