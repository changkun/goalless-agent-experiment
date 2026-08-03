"""Interactive terminal front end for 2048."""
import os
import sys

from .core import Game

try:
    import termios
    import tty
except ImportError:  # pragma: no cover - non-POSIX fallback
    termios = None
    tty = None


COLORS = {
    2: "\033[97;44m",
    4: "\033[97;45m",
    8: "\033[97;46m",
    16: "\033[97;47m",
    32: "\033[30;43m",
    64: "\033[97;42m",
    128: "\033[30;46m",
    256: "\033[97;41m",
    512: "\033[30;45m",
    1024: "\033[30;47m",
    2048: "\033[30;43m",
    4096: "\033[97;40m",
}
RESET = "\033[0m"
CLEAR = "\033[2J\033[H"


def _read_key():
    """Read a single key / arrow escape sequence from stdin."""
    key = os.read(0, 3)
    if key == b"\x1b[A":
        return "up"
    if key == b"\x1b[B":
        return "down"
    if key == b"\x1b[C":
        return "right"
    if key == b"\x1b[D":
        return "left"
    if key in (b"\x1b",):
        # Arrow keys send ESC + two more bytes; a lone ESC is a quit.
        return "quit"
    if key.decode("utf-8", "ignore").strip().lower() == "q":
        return "quit"
    if key.decode("utf-8", "ignore").lower() in ("h", "a"):
        return "left"
    if key.decode("utf-8", "ignore").lower() in ("l", "d"):
        return "right"
    if key.decode("utf-8", "ignore").lower() in ("k", "w"):
        return "up"
    if key.decode("utf-8", "ignore").lower() in ("j", "s"):
        return "down"
    return None


def render(game):
    """Render the board as a colored string."""
    lines = [f"score: {game.score}" + ("   YOU WIN!   " if game.has_won() else "")]
    for row in game.board:
        cells = []
        for value in row:
            if value == 0:
                cells.append("    ")
            else:
                color = COLORS.get(value, COLORS[4096])
                cells.append(f"{color}{value:^4}{RESET}")
        lines.append(" " + "|".join(cells))
    if game.is_game_over():
        lines.append("GAME OVER - press q to quit")
    else:
        lines.append("arrows/WASD to move, q to quit")
    return "\n".join(lines)


def play(game=None):
    """Run the interactive loop, returning the final :class:`Game`."""
    game = game or Game()
    saved = None
    if termios is not None and sys.stdin.isatty():
        saved = termios.tcgetattr(0)
        tty.setraw(0)

    try:
        while True:
            sys.stdout.write(CLEAR + render(game) + "\n")
            sys.stdout.flush()
            if game.is_game_over():
                break
            direction = _read_key()
            if direction == "quit":
                break
            if direction:
                game.move(direction)
    finally:
        if saved is not None:
            termios.tcsetattr(0, termios.TCSADRAIN, saved)
    return game
