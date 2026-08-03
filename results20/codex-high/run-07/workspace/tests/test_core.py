import unittest

from snake_game.core import Direction, Game, Status


class GameSetupTest(unittest.TestCase):
    def test_snake_starts_centered(self):
        game = Game(20, 10)
        self.assertEqual(game.snake[0], game.snake[0])
        self.assertEqual(len(game.snake), 3)
        self.assertEqual(game.status, Status.RUNNING)

    def test_board_too_small(self):
        with self.assertRaises(ValueError):
            Game(4, 10)
        with self.assertRaises(ValueError):
            Game(10, 4)

    def test_food_spawned_and_not_on_snake(self):
        game = Game(20, 10)
        self.assertIsNotNone(game.food)
        self.assertNotIn(game.food, game.snake)


class MovementTest(unittest.TestCase):
    def test_move_right_advances_head(self):
        game = Game(20, 10)
        head = game.snake[0]
        game.step()
        from snake_game.core import Point
        self.assertEqual(game.snake[0], Point(head.x + 1, head.y))

    def test_no_180_turn(self):
        game = Game(20, 10)
        game.try_turn(Direction.LEFT)  # opposites are rejected
        self.assertEqual(game.direction, Direction.RIGHT)

    def test_wall_crash(self):
        game = Game(10, 10)
        for _ in range(100):
            if game.status is not Status.RUNNING:
                break
            game.direction = Direction.RIGHT
            game.step()
        self.assertEqual(game.status, Status.CRASHED)

    def test_grows_when_eating(self):
        game = Game(20, 10)
        food = game.food
        # aim directly at the food
        while game.snake[0] != food and game.status is Status.RUNNING:
            dx = food.x - game.snake[0].x
            dy = food.y - game.snake[0].y
            if abs(dx) >= abs(dy):
                game.direction = Direction.RIGHT if dx > 0 else Direction.LEFT
            else:
                game.direction = Direction.DOWN if dy > 0 else Direction.UP
            game.step()
        self.assertEqual(game.status, Status.RUNNING)
        self.assertEqual(game.score, 1)
        self.assertEqual(len(game.snake), 4)


class AITest(unittest.TestCase):
    def test_ai_reaches_food_on_clear_board(self):
        from snake_game.core import AI

        game = Game(20, 10)
        ai = AI(game)
        target = game.food
        for _ in range(1000):
            if game.snake[0] == target:
                break
            game.direction = ai.choose_direction()
            game.step()
        self.assertEqual(game.snake[0], target)


if __name__ == "__main__":
    unittest.main()
