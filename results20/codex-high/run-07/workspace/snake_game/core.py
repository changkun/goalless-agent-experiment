"""Pure game logic for Snake, independent of any rendering."""

from __future__ import annotations

import random
from dataclasses import dataclass
from enum import Enum
from typing import Optional


class Direction(Enum):
    UP = (0, -1)
    DOWN = (0, 1)
    LEFT = (-1, 0)
    RIGHT = (1, 0)

    @property
    def dx(self) -> int:
        return self.value[0]

    @property
    def dy(self) -> int:
        return self.value[1]

    @property
    def opposite(self) -> "Direction":
        return {
            Direction.UP: Direction.DOWN,
            Direction.DOWN: Direction.UP,
            Direction.LEFT: Direction.RIGHT,
            Direction.RIGHT: Direction.LEFT,
        }[self]


class Status(Enum):
    RUNNING = "running"
    WON = "won"
    CRASHED = "crashed"


@dataclass(frozen=True)
class Point:
    x: int
    y: int

    def __add__(self, other: "Point") -> "Point":
        return Point(self.x + other.x, self.y + other.y)

    def __sub__(self, other: "Point") -> "Point":
        return Point(self.x - other.x, self.y - other.y)


class Game:
    """Stores the full state of a Snake game."""

    def __init__(self, width: int = 20, height: int = 10, seed: Optional[int] = None):
        if width < 5 or height < 5:
            raise ValueError("Board must be at least 5x5")
        self.width = width
        self.height = height
        self.rng = random.Random(seed)

        cx, cy = width // 2, height // 2
        self.snake = [Point(cx, cy), Point(cx - 1, cy), Point(cx - 2, cy)]
        self.direction = Direction.RIGHT
        self.status = Status.RUNNING
        self.score = 0
        self.steps = 0
        self.food: Optional[Point] = None
        self.spawn_food()

    def _free_cells(self) -> list[Point]:
        occupied = set(self.snake)
        free = [Point(x, y) for y in range(self.height) for x in range(self.width) if Point(x, y) not in occupied]
        return free

    def spawn_food(self) -> None:
        free = self._free_cells()
        if not free:
            self.food = None
            return
        self.food = self.rng.choice(free)

    def try_turn(self, direction: Direction) -> None:
        if direction is not self.direction.opposite:
            self.direction = direction

    def step(self) -> None:
        """Advance the game by one tick."""
        if self.status is not Status.RUNNING:
            return

        head = self.snake[0]
        new_head = Point(head.x + self.direction.dx, head.y + self.direction.dy)

        out_of_bounds = not (0 <= new_head.x < self.width and 0 <= new_head.y < self.height)

        will_grow = self.food is not None and new_head == self.food

        if out_of_bounds:
            self.status = Status.CRASHED
            return

        # The tail cell only vacates this tick unless we grow. When growing, the
        # tail stays, so include the full body in the collision check.
        body_cells = self.snake if will_grow else self.snake[:-1]
        if new_head in set(body_cells):
            self.status = Status.CRASHED
            return

        self.snake.insert(0, new_head)
        if will_grow:
            self.score += 1
            self.spawn_food()
        else:
            self.snake.pop()

        self.steps += 1

        if self.food is None:
            self.status = Status.WON


def step(game: Game) -> None:
    """Convenience function: advance a game by one tick."""
    game.step()


class AI:
    """A very simple greedy AI that heads toward the food."""

    def __init__(self, game: Game):
        self.game = game

    def choose_direction(self) -> Direction:
        head = self.game.snake[0]
        food = self.game.food
        if food is None:
            return self.game.direction

        dx = food.x - head.x
        dy = food.y - head.y

        pref = []
        if abs(dx) >= abs(dy):
            pref.append(Direction.RIGHT if dx > 0 else Direction.LEFT)
            pref.append(Direction.DOWN if dy > 0 else Direction.UP)
            pref.append(Direction.DOWN if dy <= 0 else Direction.UP)
            pref.append(Direction.RIGHT if dx <= 0 else Direction.LEFT)
        else:
            pref.append(Direction.DOWN if dy > 0 else Direction.UP)
            pref.append(Direction.RIGHT if dx > 0 else Direction.LEFT)
            pref.append(Direction.RIGHT if dx <= 0 else Direction.LEFT)
            pref.append(Direction.DOWN if dy <= 0 else Direction.UP)

        for d in pref:
            if d is self.game.direction.opposite:
                continue
            nx, ny = head.x + d.dx, head.y + d.dy
            if 0 <= nx < self.game.width and 0 <= ny < self.game.height:
                if Point(nx, ny) not in set(self.game.snake[:-1]):
                    return d
        return self.game.direction
