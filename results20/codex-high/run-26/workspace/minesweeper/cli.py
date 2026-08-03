"""Interactive terminal UI for the Minesweeper game."""

from __future__ import annotations

import random

from .game import Board, GameOver, GameWon


def print_board(board: Board, show_mines: bool = False) -> None:
    """Render the board. Caller must wrap in ANSI clear sequences if desired."""
    header = "    " + " ".join(f"{c:>2}" for c in range(board.cols))
    print(header)
    print("   +" + "---" * board.cols + "--" + "---" * board.cols + "+")
    for r in range(board.rows):
        row = f"{r:>2} |"
        for c in range(board.cols):
            cell = board.cells[r][c]
            if cell.revealed:
                if cell.mine:
                    row += " * "
                elif cell.neighbors == 0:
                    row += "   "
                else:
                    row += f" {cell.neighbors} "
            elif cell.flagged:
                row += " F "
            else:
                row += " . "
        row += "|"
        print(row)
    print("   +" + "---" * board.cols + "--" + "---" * board.cols + "+")


def run_interactive(rows: int = 9, cols: int = 9, mines: int = 10) -> None:
    board = Board(rows, cols, mines, random.Random())
    print("\033[2J\033[H", end="")  # clear screen
    print(f"Minesweeper  ({rows}x{cols}, {mines} mines)")
    print("Commands: r <row> <col> = reveal | f <row> <col> = flag | q = quit\n")

    while True:
        print_board(board)
        print(f"\nMines left: {mines - sum(1 for row in board.cells for cell in row if cell.flagged)}")
        try:
            raw = input("\n> ").strip().lower()
        except (EOFError, KeyboardInterrupt):
            print()
            return
        if not raw:
            continue
        if raw == "q":
            return
        parts = raw.split()
        try:
            if parts[0] == "r":
                r, c = int(parts[1]), int(parts[2])
                board.reveal(r, c)
            elif parts[0] == "f":
                r, c = int(parts[1]), int(parts[2])
                board.toggle_flag(r, c)
            else:
                print("Unknown command. Use r/f/q.")
                continue
        except (ValueError, IndexError):
            print("Invalid input. Example: r 1 2")
            continue
        except GameWon:
            print("\033[2J\033[H", end="")
            print_board(board, show_mines=True)
            print("\n🎉 You won!")
            return
        except GameOver:
            print("\033[2J\033[H", end="")
            print_board(board, show_mines=True)
            print("\n💥 You hit a mine. Game over!")
            return
        print("\033[2J\033[H", end="")


def main() -> None:
    import argparse

    parser = argparse.ArgumentParser(description="Play Minesweeper in your terminal.")
    parser.add_argument("--rows", type=int, default=9)
    parser.add_argument("--cols", type=int, default=9)
    parser.add_argument("--mines", type=int, default=10)
    args = parser.parse_args()
    run_interactive(args.rows, args.cols, args.mines)


if __name__ == "__main__":
    main()
