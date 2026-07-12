from gameoflife.life import Board


def test_from_pattern_and_alive_cells():
    board = Board.from_pattern(
        """
        .#.
        ..#
        ###
        """
    )
    # Coordinates are relative to the stripped pattern's own lines.
    assert board.population() == 5


def test_block_still_life_is_stable():
    block = Board({(0, 0), (0, 1), (1, 0), (1, 1)})
    assert block.step() == block


def test_blinker_oscillates_with_period_two():
    horizontal = Board({(0, 0), (0, 1), (0, 2)})
    vertical = Board({(-1, 1), (0, 1), (1, 1)})

    assert horizontal.step() == vertical
    assert vertical.step() == horizontal


def test_glider_translates_after_four_steps():
    glider = Board({(0, 1), (1, 2), (2, 0), (2, 1), (2, 2)})

    board = glider
    for _ in range(4):
        board = board.step()

    expected = Board({(r + 1, c + 1) for r, c in glider.alive_cells})
    assert board == expected


def test_dead_cell_with_three_neighbors_is_born():
    board = Board({(0, 0), (0, 1), (1, 0)})
    next_board = board.step()
    assert (1, 1) in next_board.alive_cells


def test_empty_board_stays_empty():
    assert Board().step() == Board()


def test_render_produces_bounded_grid():
    board = Board({(0, 0), (1, 1)})
    rendered = board.render(padding=0)
    assert rendered == "#.\n.#"
