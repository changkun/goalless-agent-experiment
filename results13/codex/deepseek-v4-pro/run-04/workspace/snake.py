#!/usr/bin/env python3
"""Terminal snake game — arrow keys to move, q to quit."""

import curses
import random
import time


def main(stdscr):
    curses.curs_set(0)
    stdscr.nodelay(1)
    stdscr.timeout(100)

    sh, sw = stdscr.getmaxyx()
    # Draw walls
    w = sw - 2
    h = sh - 2
    stdscr.border()

    # Snake init
    snake = [(h // 2, w // 2)]
    direction = (0, 1)  # right
    dx, dy = direction

    food = _spawn_food(snake, h, w)
    score = 0

    while True:
        key = stdscr.getch()
        if key == ord("q"):
            break
        elif key == curses.KEY_UP and direction != (1, 0):
            dy, dx = -1, 0
        elif key == curses.KEY_DOWN and direction != (-1, 0):
            dy, dx = 1, 0
        elif key == curses.KEY_LEFT and direction != (0, 1):
            dy, dx = 0, -1
        elif key == curses.KEY_RIGHT and direction != (0, -1):
            dy, dx = 0, 1

        direction = (dy, dx)
        head = snake[0]
        new_head = (head[0] + dy, head[1] + dx)

        # Wall / self collision
        if (
            new_head[0] <= 0
            or new_head[0] >= h + 1
            or new_head[1] <= 0
            or new_head[1] >= w + 1
            or new_head in snake
        ):
            break

        snake.insert(0, new_head)
        if new_head == food:
            score += 1
            food = _spawn_food(snake, h, w)
        else:
            snake.pop()

        # Render
        stdscr.clear()
        stdscr.border()
        for y, x in snake:
            try:
                stdscr.addch(y, x, "█")
            except curses.error:
                pass
        try:
            stdscr.addch(food[0], food[1], "🍎")
        except curses.error:
            try:
                stdscr.addch(food[0], food[1], "O")
            except curses.error:
                pass
        stdscr.addstr(0, 2, f" Score: {score} ")
        stdscr.refresh()

    # Game over
    stdscr.clear()
    stdscr.border()
    msg = f"GAME OVER — Score: {score}"
    stdscr.addstr(sh // 2, sw // 2 - len(msg) // 2, msg)
    stdscr.addstr(sh // 2 + 1, sw // 2 - 10, "Press any key to exit")
    stdscr.refresh()
    stdscr.nodelay(0)
    stdscr.getch()


def _spawn_food(snake, h, w):
    while True:
        f = (random.randint(1, h), random.randint(1, w))
        if f not in snake:
            return f


if __name__ == "__main__":
    curses.wrapper(main)
