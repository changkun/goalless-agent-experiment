#!/usr/bin/env python3
"""Terminal Minesweeper - pure standard library, no dependencies."""

import os
import random
import sys


def clear():
    os.system("cls" if os.name == "nt" else "clear")


def color(code, text):
    if not sys.stdout.isatty():
        return text
    return f"\x1b[{code}m{text}\x1b[0m"


class Minesweeper:
    def __init__(self, rows=9, cols=9, mines=10):
        self.rows = rows
        self.cols = cols
        self.mines = mines
        self.board = [[0] * cols for _ in range(rows)]
        self.revealed = [[False] * cols for _ in range(rows)]
        self.flagged = [[False] * cols for _ in range(rows)]
        self.first = True
        self.lost = False
        self.won = False

    def place_mines(self, safe_r, safe_c):
        cells = [(r, c) for r in range(self.rows) for c in range(self.cols)
                 if abs(r - safe_r) > 1 or abs(c - safe_c) > 1]
        random.shuffle(cells)
        for r, c in cells[: self.mines]:
            self.board[r][c] = -1
        for r in range(self.rows):
            for c in range(self.cols):
                if self.board[r][c] == -1:
                    continue
                for dr in (-1, 0, 1):
                    for dc in (-1, 0, 1):
                        nr, nc = r + dr, c + dc
                        if 0 <= nr < self.rows and 0 <= nc < self.cols \
                                and self.board[nr][nc] == -1:
                            self.board[r][c] += 1

    def reveal(self, r, c):
        if not (0 <= r < self.rows and 0 <= c < self.cols):
            return
        if self.revealed[r][c] or self.flagged[r][c]:
            return
        if self.first:
            self.place_mines(r, c)
            self.first = False
        self.revealed[r][c] = True
        if self.board[r][c] == -1:
            self.lost = True
            return
        if self.board[r][c] == 0:
            for dr in (-1, 0, 1):
                for dc in (-1, 0, 1):
                    if dr or dc:
                        self.reveal(r + dr, c + dc)

    def toggle_flag(self, r, c):
        if not (0 <= r < self.rows and 0 <= c < self.cols):
            return
        if self.revealed[r][c]:
            return
        self.flagged[r][c] = not self.flagged[r][c]

    def check_win(self):
        for r in range(self.rows):
            for c in range(self.cols):
                if self.board[r][c] != -1 and not self.revealed[r][c]:
                    return False
        return not self.lost

    def render(self):
        legend = {
            -1: color("31", " * "),
            0: " . ",
            1: color("34", " 1 "),
            2: color("32", " 2 "),
            3: color("33", " 3 "),
            4: color("35", " 4 "),
            5: color("36", " 5 "),
        }
        lines = []
        lines.append("    " + " ".join(f"{c:>2}" for c in range(self.cols)))
        lines.append("")
        for r in range(self.rows):
            row = [f"{r:>2}  "]
            for c in range(self.cols):
                if self.flagged[r][c]:
                    cell = color("1;37", " F ")
                elif self.board[r][c] == -1 and self.lost:
                    cell = color("31", " * ")
                elif self.revealed[r][c]:
                    cell = legend.get(self.board[r][c], color("31", " ? "))
                else:
                    cell = "[ ]"
                row.append(cell)
            lines.append("".join(row))
        return "\n".join(lines)


def main():
    rows = int(input(f"rows [{10}]: ") or 10)
    cols = int(input(f"cols [{10}]: ") or 10)
    total = rows * cols
    default_mines = max(1, total // 8)
    mines = int(input(f"mines [{default_mines}]: ") or default_mines)
    mines = min(mines, total - 1)

    g = Minesweeper(rows, cols, mines)
    clear()
    print(color("1;36", "   MINESWEEPER   "))
    print("commands: 'r c' reveal | 'f r c' flag | 'q' quit\n")

    while not g.lost and not g.won:
        print(g.render())
        print(f"\nmines left: {mines - sum(sum(r) for r in g.flagged)}")
        cmd = input("> ").strip().lower()
        clear()
        if cmd == "q":
            print("bye!")
            return
        parts = cmd.split()
        try:
            if parts[0] == "f" and len(parts) == 3:
                g.toggle_flag(int(parts[1]), int(parts[2]))
            elif len(parts) == 2:
                g.reveal(int(parts[0]), int(parts[1]))
            else:
                print("hmm? use: 'r c', 'f r c', or 'q'")
        except ValueError:
            print("hmm? use: 'r c', 'f r c', or 'q'")

        g.won = g.check_win()

    clear()
    print(g.render())
    if g.lost:
        print(color("1;31", "\n  BOOM! You hit a mine.\n"))
    else:
        print(color("1;32", "\n  YOU WIN! All safe cells revealed.\n"))


if __name__ == "__main__":
    try:
        main()
    except (KeyboardInterrupt, EOFError):
        print("\nbye!")
