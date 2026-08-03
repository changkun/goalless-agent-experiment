"""Interactive terminal front-end for Minesweeper."""

from __future__ import annotations

import sys

from .game import Game


# ANSI colors, only enabled on TTYs or when forced.
class Style:
    def __init__(self, enabled: bool) -> None:
        self.enabled = enabled
        self.codes = {
            "reset": "\033[0m",
            "red": "\033[91m",
            "green": "\033[92m",
            "yellow": "\033[93m",
            "blue": "\033[94m",
            "magenta": "\033[95m",
            "cyan": "\033[96m",
            "grey": "\033[90m",
            "bold": "\033[1m",
        }

    def paint(self, text: str, *names: str) -> str:
        if not self.enabled:
            return text
        prefix = "".join(self.codes[n] for n in names)
        return f"{prefix}{text}{self.codes['reset']}"


COUNTER_COLORS = {
    0: "grey",
    1: "blue",
    2: "green",
    3: "red",
    4: "magenta",
    5: "yellow",
    6: "cyan",
    7: "red",
    8: "green",
}


class Board:
    """Render the board to a string to enable testing."""

    def __init__(self, game: Game, style: Style | None = None) -> None:
        self.game = game
        self.style = style or Style(False)

    def render(self, show_mines: bool = False) -> str:
        g = self.game
        out = [f"   " + " ".join(f"{x}" for x in range(g.width))]
        out.append("   " + "--" * g.width)
        for y in range(g.height):
            row = [f"{y:>2}|"]
            for x in range(g.width):
                cell = g.cells[g.index(x, y)]
                row.append(self._cell_char(cell, show_mines))
            out.append(" ".join(row))
        return "\n".join(out)

    def _cell_char(self, cell, show_mines: bool) -> str:
        if show_mines and cell.mine:
            return self.style.paint("*", "red", "bold")
        if cell.flagged:
            return self.style.paint("F", "yellow")
        if not cell.revealed:
            return "."
        if cell.adjacent == 0:
            return " "
        return self.style.paint(str(cell.adjacent), COUNTER_COLORS[cell.adjacent], "bold")


def parse_command(raw: str) -> tuple[str, int, int] | None:
    """Parse ``r``/``f`` commands like ``r 3 4`` or ``3 4``. Returns None if malformed."""
    parts = raw.strip().replace(",", " ").split()
    if not parts:
        return None
    if parts[0].lower() in ("r", "reveal"):
        parts = parts[1:]
        action = "reveal"
    elif parts[0].lower() in ("f", "flag"):
        parts = parts[1:]
        action = "flag"
    else:
        action = "reveal"
    if len(parts) != 2:
        return None
    try:
        x, y = int(parts[0]), int(parts[1])
    except ValueError:
        return None
    return action, x, y


def main(argv: list[str] | None = None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    force_color = "--color" in argv

    style = Style(sys.stdout.isatty() or force_color)
    game = Game()
    board = Board(game, style)

    print(style.paint("MINESWEEPER", "bold", "cyan"))
    print(f"{game.width}x{game.height} board, {game.mines} mines.")
    print("Commands: `r x y` to reveal, `f x y` to flag, `q` to quit.\n")

    try:
        while True:
            print(board.render())
            print(style.paint(f"Flags left: {game.flags_remaining()}", "grey"))

            if game.won:
                flag = style.paint("You win!", "green", "bold")
                print(flag + " All safe cells revealed.")
                return 0
            if game.lost:
                flag = style.paint("Boom. You hit a mine!", "red", "bold")
                print(flag)
                return 1

            try:
                raw = input("> ")
            except EOFError:
                print()
                return 0

            if raw.strip().lower() in ("q", "quit", "exit"):
                return 0

            parsed = parse_command(raw)
            if parsed is None:
                print(style.paint("Usage: `r x y`, `f x y`, or `q`.", "yellow"))
                continue
            action, x, y = parsed
            if not game.in_bounds(x, y):
                print(style.paint(f"({x}, {y}) is off the board.", "yellow"))
                continue
            if action == "flag":
                game.toggle_flag(x, y)
            else:
                game.reveal(x, y)
            print()
    finally:
        pass


if __name__ == "__main__":
    raise SystemExit(main())
