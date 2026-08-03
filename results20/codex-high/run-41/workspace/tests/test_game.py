import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from minesweeper.game import Board, parse_coord


def test_mine_placement_avoids_first_click():
    b = Board.create(9, 9, 10)
    assert b.first_move is True
    ok = b.reveal(0, 0)
    assert ok is True
    assert b.first_move is False
    assert b.revealed[0][0] is True
    total = sum(row.count(-1) for row in b.grid)
    assert total == 10
    for r in range(0, 2):
        for c in range(0, 2):
            assert b.grid[r][c] != -1
    for r in range(b.rows):
        for c in range(b.cols):
            if b.grid[r][c] != -1:
                cnt = sum(1 for nr, nc in b.neighbors(r, c) if b.grid[nr][nc] == -1)
                assert b.grid[r][c] == cnt


def test_flag_toggle_and_remaining():
    b = Board.create(9, 9, 10)
    b.grid = [[0, 0, -1], [0, 0, 0], [-1, 0, 0]]
    b.revealed = [[False] * 3 for _ in range(3)]
    b.first_move = False
    b.toggle_flag(0, 2)
    assert b.flagged[0][2] is True
    assert b.remaining_mines() == 9
    b.toggle_flag(0, 2)
    assert b.remaining_mines() == 10


def test_flagged_cell_not_revealed_by_flood_fill():
    b = Board.create(9, 9, 10)
    b.grid = [[0, 1, -1] + [8] * 6,
              [0, 1, 1] + [8] * 6,
              [0, 0, 0] + [8] * 6,
              [8] * 9, [8] * 9, [8] * 9]
    b.revealed = [[False] * 9 for _ in range(9)]
    b.flagged = [[False] * 9 for _ in range(9)]
    b.first_move = False
    b.toggle_flag(2, 2)
    b.reveal(0, 0)
    assert b.revealed[0][0] is True
    assert b.revealed[2][2] is False


def test_win_detection():
    b = Board.create(2, 2, 1)
    b.grid = [[0, -1], [1, 1]]
    b.revealed = [[False, False], [False, False]]
    assert b.is_won() is False
    b.revealed = [[True, False], [True, True]]
    assert b.is_won() is True


def test_parse_coord():
    assert parse_coord("2 3", 9, 9) == (2, 3)
    assert parse_coord("2,3", 9, 9) == (2, 3)
