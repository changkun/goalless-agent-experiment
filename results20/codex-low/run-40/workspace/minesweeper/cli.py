"""Command-line interface for the Minesweeper game."""

from __future__ import annotations

import argparse
import random
import sys

from .game import Board, CellState

CELL_DISPLAY = {
    "hidden": "·",
    "flagged": "⚑",
    "revealed": " ",
}

MINE_DISPLAY = "💣"


class _ExitingBrokenPipe(Exception):
    pass


def _parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="minesweeper",
        description="Play a game of Minesweeper in the terminal.",
    )
    parser.add_argument(
        "-r", "--rows", type=int, default=9, help="Number of rows (default: 9)"
    )
    parser.add_argument(
        "-c", "--cols", type=int, default=9, help="Number of columns (default: 9)"
    )
    parser.add_argument(
        "-m",
        "--mines",
        type=int,
        default=None,
        help="Number of mines (default: ~15%% of cells)",
    )
    parser.add_argument(
        "-s",
        "--seed",
        type=int,
        default=None,
        help="Random seed for reproducible boards",
    )
    return parser.parse_args(argv)


def _resolve_mine_count(args: argparse.Namespace) -> int:
    total = args.rows * args.cols
    if args.mines is not None:
        return args.mines
    return max(1, round(total * 0.15))


def _fmt_cell(board: Board, row: int, col: int) -> str:
    cell = board.state[row][col]
    if cell != CellState.REVEALED:
        return CELL_DISPLAY[cell]
    if (row, col) in board.mines_positions:
        return MINE_DISPLAY
    count = board.counts[row][col]
    return str(count) if count else " "


def _render(board: Board) -> str:
    col_gutter = len(str(board.cols - 1))
    lines: list[str] = []

    header = " " * (len(str(board.rows - 1)) + 1)
    header += " ".join(str(c).rjust(col_gutter) for c in range(board.cols))
    lines.append(header)

    for r in range(board.rows):
        row_label = str(r).rjust(len(str(board.rows - 1)))
        cells = " ".join(_fmt_cell(board, r, c).rjust(col_gutter) for c in range(board.cols))
        lines.append(f"{row_label} {cells}")

    mine_indicator = f"{board.flagged}/{board.mines} flags"
    return "\n".join(lines) + f"\n{mine_indicator.rjust(len(header))}"


def _prompt() -> str:
    return input("> ").strip().lower()


def _process_command(
    board: Board, command: str
) -> tuple[bool, str]:
    """Handle a single command, returning (keep_playing, message)."""
    parts = command.split()
    if not parts:
        return True, ""

    action = parts[0]
    try:
        numbers = [int(x) for x in parts[1:2]]
        if len(numbers) != 1:
            return True, "Usage: reveal|flag|q [row col]"
        row, col = divmod(numbers[0], board.cols)
    except ValueError:
        return True, "Usage: reveal|flag|q [row col]"

    if action in ("q", "quit", "exit"):
        return False, "Quit."
    if action not in ("r", "reveal", "f", "flag"):
        return True, "Unknown command."

    try:
        if action in ("f", "flag"):
            board.flag(row, col)
            return True, ""
        lost = board.reveal(row, col)
        if lost:
            return False, "💥 Boom! You hit a mine."
        if board.won:
            return False, "🎉 You win!"
        return True, ""
    except IndexError as exc:
        return True, str(exc)


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(argv)
    if args.rows < 1 or args.cols < 1:
        print("Rows and columns must be positive.", file=sys.stderr)
        return 2

    board = Board(args.rows, args.cols, _resolve_mine_count(args), random.Random(args.seed))
    print(f"Minesweeper {args.rows}x{args.cols} with {board.mines} mines")
    print("Commands: reveal <cell> | flag <cell> | quit")
    print("Cells are zero-indexed (row * cols + col).")
    print(_render(board))

    keep_playing = True
    while keep_playing:
        try:
            command = _prompt()
        except EOFError:
            print("\nQuit.")
            break
        except KeyboardInterrupt:
            print("\nQuit.")
            break

        keep_playing, message = _process_command(board, command)
        if message:
            print(message)
        if keep_playing:
            print(_render(board))

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
