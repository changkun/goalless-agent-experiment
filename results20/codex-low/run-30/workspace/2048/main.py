#!/usr/bin/env python3
"""Play 2048 in the terminal.

Keys: arrow keys or hjkl to move, ``n`` for a new game, ``q`` to quit.
Requires a TTY; run ``python3 main.py`` directly.
"""

from __future__ import annotations

import sys
import time
from typing import Optional, Tuple

from engine.core import Game, Move

ANSI_RESET = "\x1b[0m"
ANSI_BOLD = "\x1b[1m"
ANSI_CLEAR = "\x1b[2J\x1b[H"
ANSI_HIDE_CURSOR = "\x1b[?25l"
ANSI_SHOW_CURSOR = "\x1b[?25h"

TILE_COLORS = {
    0: "\x1b[48;5;236m",
    2: "\x1b[48;5;231m",
    4: "\x1b[48;5;229m",
    8: "\x1b[48;5;215m",
    16: "\x1b[48;5;209m",
    32: "\x1b[48;5;203m",
    64: "\x1b[48;5;196m",
    128: "\x1b[48;5;220m",
    256: "\x1b[48;5;221m",
    512: "\x1b[48;5;222m",
    1024: "\x1b[48;5;226m",
    2048: "\x1b[48;5;46m",
    4096: "\x1b[48;5;45m",
    8192: "\x1b[48;5;27m",
}

KEY_TO_MOVE = {
    "\x1b[A": Move.UP,
    "\x1b[B": Move.DOWN,
    "\x1b[C": Move.RIGHT,
    "\x1b[D": Move.LEFT,
    "w": Move.UP,
    "s": Move.DOWN,
    "a": Move.LEFT,
    "d": Move.RIGHT,
    "k": Move.UP,
    "j": Move.DOWN,
    "h": Move.LEFT,
    "l": Move.RIGHT,
}


def tile_color(value: int) -> str:
    """Return the ANSI background for a tile value, falling back gracefully."""
    return TILE_COLORS.get(value, "\x1b[48;5;88m")


def render(game: Game) -> str:
    """Build the full screen string for the current game state."""
    cell_width = max(len(str(tile)) for tile in game.board)
    cell_width = max(cell_width, 3) + 2
    lines = [ANSI_CLEAR, ANSI_BOLD + "  2 0 4 8" + ANSI_RESET, ""]
    header = f"  score: {game.score:<6}  moves: {game.moves}"
    if game.won:
        header += "  " + ANSI_BOLD + "YOU WIN!" + ANSI_RESET
    lines.append(header)
    lines.append("")
    for row in range(game.size):
        line = "  "
        for col in range(game.size):
            value = game.board[row * game.size + col]
            label = str(value) if value else "·"
            cell = f"{label:^{cell_width}}"
            line += tile_color(value) + " " + cell + " " + ANSI_RESET
        lines.append(line)
        lines.append("")
    if game.is_game_over():
        lines.append(ANSI_BOLD + "  GAME OVER" + ANSI_RESET)
    else:
        lines.append("  arrows / hjkl to move · n new game · q quit")
    return "\n".join(lines)


def _read_key() -> Optional[str]:
    """Read one keypress from stdin (arrow keys arrive as 3 bytes)."""
    first = sys.stdin.read(1)
    if not first:
        return None
    if first == "\x1b":
        rest = sys.stdin.read(2)
        if rest:
            return first + rest
    return first


def _to_move(key: str) -> Optional[Move]:
    return KEY_TO_MOVE.get(key)


def play(game: Optional[Game] = None) -> int:
    """Run the interactive game loop. Returns the final score."""
    if game is None:
        game = Game()
    if not sys.stdin.isatty():
        raise RuntimeError("interactive mode needs a TTY; use --text for scripts")
    sys.stdout.write(ANSI_HIDE_CURSOR)
    try:
        while True:
            sys.stdout.write(render(game))
            sys.stdout.flush()
            key = _read_key()
            if key is None:
                break
            if key == "q":
                break
            if key == "n":
                game = Game(size=game.size)
                continue
            move = _to_move(key)
            if move is not None:
                result = game.move(move)
                if result.won and not hasattr(play, "_celebrated"):
                    sys.stdout.write(ANSI_CLEAR + ANSI_BOLD + "  YOU WON! Keep going (n) or quit (q)." + ANSI_RESET + "\n")
                    sys.stdout.flush()
                    play._celebrated = True  # type: ignore[attr-defined]
                    time.sleep(1.2)
    finally:
        sys.stdout.write(ANSI_SHOW_CURSOR)
    sys.stdout.write("\n")
    return game.score


_TEXT_MOVES = {"w": Move.UP, "s": Move.DOWN, "a": Move.LEFT, "d": Move.RIGHT}


def _text_mode(size: int, moves: str) -> int:
    """Scripted mode: apply a sequence of wasd moves and print the board."""
    game = Game(size=size)
    for raw in moves:
        move = _TEXT_MOVES.get(raw.lower())
        if move is None:
            raise ValueError(f"unknown move: {raw!r} (use wasd)")
        game.move(move)
    for row in range(game.size):
        print(
            " ".join(
                str(game.board[row * game.size + col]).rjust(5)
                for col in range(game.size)
            )
        )
    print(f"score: {game.score}")
    return game.score


def main(argv: Optional[list] = None) -> int:
    import argparse

    parser = argparse.ArgumentParser(
        prog="2048",
        description="Play 2048 in your terminal.",
    )
    parser.add_argument("--size", type=int, default=4, help="board size (default 4)")
    parser.add_argument(
        "--text",
        metavar="MOVES",
        help="play a scripted sequence of wasd moves and print the result",
    )
    args = parser.parse_args(argv)

    try:
        if args.text is not None:
            return _text_mode(args.size, args.text)
        return play(Game(size=args.size))
    except (KeyboardInterrupt, EOFError):
        sys.stdout.write(ANSI_SHOW_CURSOR + "\n")
        return 0
    except (RuntimeError, ValueError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
