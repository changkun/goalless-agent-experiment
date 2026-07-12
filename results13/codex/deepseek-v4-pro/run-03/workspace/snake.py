#!/usr/bin/env python3
"""Snake — a classic terminal arcade game."""
import curses
import random
import time
from collections import deque

DIRECTIONS = {
    curses.KEY_UP:    (-1, 0),
    curses.KEY_DOWN:  (1, 0),
    curses.KEY_LEFT:  (0, -1),
    curses.KEY_RIGHT: (0, 1),
    ord('w'): (-1, 0),
    ord('s'): (1, 0),
    ord('a'): (0, -1),
    ord('d'): (0, 1),
}
OPPOSITE = {(-1, 0): (1, 0), (1, 0): (-1, 0), (0, -1): (0, 1), (0, 1): (0, -1)}

def main(stdscr):
    curses.curs_set(0)
    stdscr.nodelay(True)
    stdscr.timeout(120)

    sh, sw = stdscr.getmaxyx()
    h, w = sh - 2, sw - 2  # pad 1 cell on each side

    # Spawn the snake roughly centered
    snake = deque()
    head_y, head_x = h // 2, w // 2
    for i in range(3):
        snake.append((head_y, head_x + i))

    direction = (0, -1)  # start moving left
    food = _spawn_food(snake, h, w)
    score = 0
    paused = False

    while True:
        key = stdscr.getch()

        if key == ord('q'):
            return
        if key == ord(' ') or key == ord('p'):
            paused = not paused
        if not paused and key in DIRECTIONS:
            new_dir = DIRECTIONS[key]
            if new_dir != OPPOSITE.get(direction):
                direction = new_dir

        if paused:
            stdscr.addstr(sh // 2, sw // 2 - 8, "⏸  PAUSED  (space / p)", curses.A_BOLD)
            stdscr.refresh()
            continue

        # Move
        dy, dx = direction
        new_head = (snake[0][0] + dy, snake[0][1] + dx)
        snake.appendleft(new_head)

        # Check food
        if new_head == food:
            score += 1
            food = _spawn_food(snake, h, w)
        else:
            snake.pop()

        # Collision: walls
        y, x = new_head
        if y < 0 or y >= h or x < 0 or x >= w:
            _game_over(stdscr, sh, sw, score)
            return

        # Collision: self
        if new_head in list(snake)[1:]:
            _game_over(stdscr, sh, sw, score)
            return

        _draw(stdscr, snake, food, h, w, score)
        time.sleep(0.01)

def _spawn_food(snake, h, w):
    while True:
        pos = (random.randint(0, h - 1), random.randint(0, w - 1))
        if pos not in snake:
            return pos

def _draw(stdscr, snake, food, h, w, score):
    stdscr.erase()
    # Border
    stdscr.border(0)
    stdscr.addstr(0, 2, f"  🐍 Snake  │  Score: {score}  │  Q=quit  P=pause  ")

    # Food
    fy, fx = food
    stdscr.addstr(fy + 1, fx + 1, "🍎")

    # Snake body
    head = snake[0]
    for i, (y, x) in enumerate(snake):
        ch = "●" if i == 0 else "○"
        try:
            stdscr.addstr(y + 1, x + 1, ch)
        except curses.error:
            pass

    # Direction indicator near head
    stdscr.addstr(head[0] + 1, head[1] + 1, "●")
    stdscr.refresh()

def _game_over(stdscr, sh, sw, score):
    stdscr.clear()
    stdscr.addstr(sh // 2, sw // 2 - 10, "💀  GAME OVER  💀", curses.A_BOLD)
    stdscr.addstr(sh // 2 + 2, sw // 2 - 8, f"Final Score: {score}")
    stdscr.addstr(sh // 2 + 4, sw // 2 - 12, "Press any key to exit...")
    stdscr.nodelay(False)
    stdscr.getch()

if __name__ == "__main__":
    curses.wrapper(main)
