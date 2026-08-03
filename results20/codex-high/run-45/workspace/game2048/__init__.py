"""2048 — a classic sliding-tile puzzle, playable in the terminal."""

from game2048.game2048 import (
    Game,
    WINNING_TILE,
    available_moves,
    empty_board,
    has_won,
    is_game_over,
    move,
    move_and_spawn,
    spawn_tile,
)

__all__ = [
    "Game",
    "WINNING_TILE",
    "available_moves",
    "empty_board",
    "has_won",
    "is_game_over",
    "move",
    "move_and_spawn",
    "spawn_tile",
]

__version__ = "1.0.0"
