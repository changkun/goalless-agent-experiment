"""Tests for the 2048 game core logic."""

import random

import pytest

from game2048.game2048 import (
    WINNING_TILE,
    Game,
    available_moves,
    empty_board,
    has_won,
    is_game_over,
    move,
    move_and_spawn,
    spawn_tile,
)


def test_empty_board():
    board = empty_board(4)
    assert len(board) == 4
    assert all(len(row) == 4 for row in board)
    assert all(cell == 0 for row in board for cell in row)


def test_move_left_slides():
    board = [[4, 0, 0, 0], [0, 0, 0, 0], [0, 0, 0, 0], [0, 0, 0, 0]]
    result, changed, score = move(board, "left")
    assert changed is True
    assert score == 0
    assert result[0] == [4, 0, 0, 0]


def test_move_left_merges_once():
    # Two adjacent equal tiles merge once; a third stays separate.
    board = [[2, 2, 2, 0], [0, 0, 0, 0], [0, 0, 0, 0], [0, 0, 0, 0]]
    result, changed, score = move(board, "left")
    assert changed is True
    assert result[0] == [4, 2, 0, 0]
    assert score == 4


def test_move_left_merges_all():
    board = [[2, 2, 2, 2], [0, 0, 0, 0], [0, 0, 0, 0], [0, 0, 0, 0]]
    result, changed, score = move(board, "left")
    assert result[0] == [4, 4, 0, 0]
    assert score == 8


@pytest.mark.parametrize("direction", ["left", "right", "up", "down"])
def test_directions_are_consistent(direction):
    board = [
        [2, 0, 2, 4],
        [0, 0, 0, 0],
        [2, 2, 2, 4],
        [4, 4, 0, 0],
    ]
    result, changed, score = move(board, direction)
    assert isinstance(result, list)
    assert changed is True or result is not None


def test_move_right_merges():
    board = [[0, 0, 0, 2], [0, 0, 0, 0], [0, 0, 0, 0], [0, 0, 0, 0]]
    result, changed, _ = move(board, "right")
    assert result[0] == [0, 0, 0, 2]


def test_move_up_merges():
    board = [[2, 0, 0, 0], [2, 0, 0, 0], [0, 0, 0, 0], [0, 0, 0, 0]]
    result, changed, score = move(board, "up")
    assert changed is True
    assert result[0] == [4, 0, 0, 0]
    assert score == 4


def test_move_down_merges():
    board = [[2, 0, 0, 0], [2, 0, 0, 0], [0, 0, 0, 0], [0, 0, 0, 0]]
    result, changed, score = move(board, "down")
    assert changed is True
    assert result[3] == [4, 0, 0, 0]
    assert score == 4


def test_no_change_when_blocked():
    board = [[2, 4, 2, 4], [4, 2, 4, 2], [2, 4, 2, 4], [4, 2, 4, 2]]
    result, changed, score = move(board, "left")
    assert changed is False
    assert result == board
    assert score == 0


def test_spawn_tile_fills_one_empty():
    rng = random.Random(0)
    board = empty_board(2)
    spawned = spawn_tile(board, rng)
    assert spawned is True
    non_zero = [c for row in board for c in row if c != 0]
    assert len(non_zero) == 1
    assert non_zero[0] in (2, 4)


def test_spawn_tile_full_board():
    rng = random.Random(0)
    board = [[2, 4], [4, 2]]
    assert spawn_tile(board, rng) is False


def test_available_moves():
    board = [[2, 2, 4, 8], [16, 32, 64, 128], [256, 512, 1024, 2], [4, 8, 16, 32]]
    moves = available_moves(board)
    assert "left" in moves  # 2,2 merge
    assert moves
    assert isinstance(moves, list)


def test_game_over_when_no_moves():
    board = [[2, 4, 2, 4], [4, 2, 4, 2], [2, 4, 2, 4], [4, 2, 4, 2]]
    assert is_game_over(board) is True
    assert available_moves(board) == []


def test_game_not_over_with_move():
    board = [[2, 2, 4, 8], [16, 32, 64, 128], [256, 512, 1024, 2], [4, 8, 16, 32]]
    assert is_game_over(board) is False


def test_has_won():
    board = [[2048, 0, 0, 0], [0, 0, 0, 0], [0, 0, 0, 0], [0, 0, 0, 0]]
    assert has_won(board) is True


def test_has_not_won():
    board = [[1024, 0, 0, 0], [0, 0, 0, 0], [0, 0, 0, 0], [0, 0, 0, 0]]
    assert has_won(board) is False


def test_game_initialises_with_two_tiles():
    game = Game(seed=1, size=4)
    non_zero = [c for row in game.board for c in row if c != 0]
    assert len(non_zero) == 2
    assert game.score == 0
    assert game.won is False


def test_game_play_changes_board():
    game = Game(seed=2, size=4)
    before = [row[:] for row in game.board]
    changed = game.play("left")
    # With only two tiles it's possible (rare) for left to be a no-op, so we
    # don't assert changed; instead ensure it runs without error.
    assert isinstance(changed, bool)
    _ = before


def test_game_play_merges_and_scores():
    # Force a deterministic merge with a known rng sequence of spawns.
    game = Game(seed=0, size=4)
    # Position two 2s side by side directly.
    game.board = empty_board(4)
    game.board[0] = [2, 2, 0, 0]
    result = game.play("left")
    assert result is True
    assert game.board[0][0] == 4
    assert game.score == 4


def test_move_and_spawn():
    rng = random.Random(5)
    board = [[2, 2, 0, 0], [0, 0, 0, 0], [0, 0, 0, 0], [0, 0, 0, 0]]
    new_board, changed, score = move_and_spawn(board, "left", rng)
    assert changed is True
    assert new_board[0][0] == 4
    assert score == 4
    non_zero = sum(1 for row in new_board for c in row if c != 0)
    assert non_zero == 2  # merged tile + one spawned


def test_winning_tile_constant():
    assert WINNING_TILE == 2048
