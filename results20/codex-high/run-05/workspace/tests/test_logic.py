import unittest

from snake_game.logic import DOWN, LEFT, RIGHT, UP, Game


class GameInitTest(unittest.TestCase):
    def test_default_board_size(self):
        g = Game.new()
        self.assertEqual(g.width, 20)
        self.assertEqual(g.height, 20)

    def test_snake_starts_centered_and_length_three(self):
        g = Game.new(width=10, height=10)
        self.assertEqual(len(g.snake), 3)
        # Head is centered, body trails to the left.
        self.assertEqual(g.snake[0], (5, 5))
        self.assertEqual(g.snake[1], (4, 5))
        self.assertEqual(g.snake[2], (3, 5))

    def test_food_not_on_snake(self):
        g = Game.new()
        self.assertNotIn(g.food, g.snake)

    def test_seed_gives_deterministic_food(self):
        a = Game.new(seed=1)
        b = Game.new(seed=1)
        c = Game.new(seed=2)
        self.assertEqual(a.food, b.food)
        self.assertNotEqual(a.food, c.food)

    def test_too_small_board_rejected(self):
        with self.assertRaises(ValueError):
            Game.new(width=3, height=3)


class StepTest(unittest.TestCase):
    def test_moves_right_by_default(self):
        g = Game.new(width=10, height=10)
        head = g.snake[0]
        g.step()
        self.assertEqual(g.snake[0], (head[0] + 1, head[1]))
        # Length unchanged when not eating.
        self.assertEqual(len(g.snake), 3)

    def test_cannot_reverse_into_own_body(self):
        g = Game.new(width=10, height=10)
        g.turn(LEFT)  # reverse of initial RIGHT -> ignored
        self.assertEqual(g.direction, RIGHT)

    def test_food_eaten_grows_and_scores(self):
        g = Game.new(width=10, height=10)
        # Force food directly ahead of the head.
        head = g.snake[0]
        g.food = (head[0] + 1, head[1])
        g.step()
        self.assertEqual(g.score, 1)
        self.assertEqual(len(g.snake), 4)

    def test_wall_collision_ends_game(self):
        g = Game.new(width=10, height=10)
        g.snake = [(9, 5), (8, 5)]  # head at right wall
        g.direction = RIGHT
        self.assertFalse(g.step())
        self.assertTrue(g.game_over)

    def test_self_collision_ends_game(self):
        g = Game.new(width=10, height=10)
        # Create a closed loop: head about to hit its own neck.
        g.snake = [(2, 2), (1, 2), (1, 1), (2, 1)]
        g.direction = LEFT  # would move head from (2,2) onto (1,2) which is body
        g.food = (9, 9)  # keep food away
        self.assertFalse(g.step())
        self.assertTrue(g.game_over)

    def test_tail_vacates_without_collision(self):
        g = Game.new(width=10, height=10)
        # Head moves onto the cell currently occupied by the tail; since the
        # tail vacates during this tick, it is not a collision.
        g.snake = [(2, 2), (1, 2)]
        g.direction = LEFT
        g.food = (9, 9)
        self.assertTrue(g.step())
        self.assertFalse(g.game_over)
        self.assertEqual(g.snake[0], (1, 2))


class TurnTest(unittest.TestCase):
    def test_valid_turn_changes_direction(self):
        g = Game.new(seed=0)
        g.turn(UP)
        self.assertEqual(g.direction, UP)

    def test_opposite_direction_ignored(self):
        g = Game.new(seed=0)
        g.direction = RIGHT
        g.turn(LEFT)
        self.assertEqual(g.direction, RIGHT)


class WinTest(unittest.TestCase):
    def test_full_board_is_win(self):
        g = Game.new(width=5, height=5, seed=0)
        # Fill every cell with the snake so no free cells remain.
        cells = [(x, y) for y in range(5) for x in range(5)]
        g.snake = cells
        g._place_food()
        self.assertTrue(g.is_won)


if __name__ == "__main__":
    unittest.main()
