"""Pure game logic for Snake, with no UI dependencies.

Coordinates are ``(x, y)`` with ``x`` growing rightward and ``y`` growing
downward. The snake is a list of cells with the head first.
"""

from __future__ import annotations

import random
from dataclasses import dataclass, field
from typing import Optional, Sequence, Tuple

Point = Tuple[int, int]

UP = (0, -1)
DOWN = (0, 1)
LEFT = (-1, 0)
RIGHT = (1, 0)

_OPPOSITE = {UP: DOWN, DOWN: UP, LEFT: RIGHT, RIGHT: LEFT}


@dataclass
class Game:
    """State of a snake game."""

    width: int
    height: int
    snake: list[Point]
    direction: Point = RIGHT
    food: Point = field(default=None)  # type: ignore[assignment]
    score: int = 0
    game_over: bool = False
    _rng: random.Random = field(default=None, repr=False)  # type: ignore[assignment]

    @classmethod
    def new(cls, width: int = 20, height: int = 20, seed: Optional[int] = None) -> "Game":
        """Create a centered snake and immediately place food."""
        if width < 5 or height < 5:
            raise ValueError("board must be at least 5x5")
        cx, cy = width // 2, height // 2
        snake = [(cx, cy), (cx - 1, cy), (cx - 2, cy)]
        game = cls(width, height, snake, _rng=random.Random(seed))
        game._place_food()
        return game

    def step(self, direction: Optional[Point] = None) -> bool:
        """Advance one tick. Returns True if the snake moved."""
        if self.game_over:
            return False

        if direction is not None:
            self.turn(direction)

        head = self.snake[0]
        new_head = (head[0] + self.direction[0], head[1] + self.direction[1])

        # Hitting a wall ends the game.
        if not (0 <= new_head[0] < self.width and 0 <= new_head[1] < self.height):
            self.game_over = True
            return False

        # The tail cell vacates this tick, so it is not a collision unless we
        # are eating (and thus the tail does not move away).
        eating = new_head == self.food
        if new_head in self.snake and (new_head != self.snake[-1] or eating):
            self.game_over = True
            return False

        self.snake.insert(0, new_head)
        if eating:
            self.score += 1
            self._place_food()
        else:
            self.snake.pop()

        return True

    def turn(self, direction: Point) -> None:
        """Change heading, rejecting a direct reversal into the body."""
        if direction != _OPPOSITE[self.direction]:
            self.direction = direction

    def _place_food(self) -> None:
        free = [
            (x, y)
            for y in range(self.height)
            for x in range(self.width)
            if (x, y) not in self.snake
        ]
        if not free:
            # Every cell is covered: the player wins.
            self.game_over = True
            self.food = None
            return
        self.food = self._rng.choice(free)

    @property
    def cells(self) -> Sequence[Point]:
        """Return the occupied snake cells, head first."""
        return self.snake

    @property
    def is_won(self) -> bool:
        return self.game_over and self.food is None
