#!/usr/bin/env python3
"""Terminal Snake — a classic snake game using the standard-library curses module."""
import curses
import random
import sys


HELP = (
    "Arrow keys / WASD: move   |   Game over: Q | Restart: R"
)


def draw_text(stdscr, y, x, text, attr=0):
    try:
        stdscr.addstr(y, x, text, attr)
    except curses.error:
        pass


def make_border(stdscr, height, width, color):
    try:
        stdscr.border()
    except curses.error:
        pass


def run(stdscr):
    curses.curs_set(0)
    stdscr.nodelay(True)

    curses.start_color()
    curses.use_default_colors()
    curses.init_pair(1, curses.COLOR_CYAN, -1)     # snake head
    curses.init_pair(2, curses.COLOR_GREEN, -1)    # snake body
    curses.init_pair(3, curses.COLOR_RED, -1)      # food
    curses.init_pair(4, curses.COLOR_YELLOW, -1)   # score / ui

    height, width = stdscr.getmaxyx()
    if height < 12 or width < 24:
        stdscr.nodelay(False)
        draw_text(stdscr, 0, 0, "Window too small (need >= 12 rows, 24 cols)")
        stdscr.refresh()
        stdscr.getch()
        return

    board_h, board_w = height - 2, width - 2
    start_y, start_x = 1, 1

    while True:
        stdscr.clear()
        make_border(stdscr, height, width, 0)
        stdscr.timeout(90)

        # Snake starts in the middle, moving right.
        mid_y, mid_x = start_y + board_h // 2, start_x + board_w // 4
        snake = [(mid_y, mid_x + i) for i in range(4)]
        dirs = {curses.KEY_UP: (-1, 0), curses.KEY_DOWN: (1, 0),
                curses.KEY_LEFT: (0, -1), curses.KEY_RIGHT: (0, 1)}
        # WASD too.
        dirs.update({ord('w'): (-1, 0), ord('s'): (1, 0),
                     ord('a'): (0, -1), ord('d'): (0, 1)})
        direction = (0, 1)
        next_direction = direction

        def spawn_food():
            while True:
                y = random.randint(start_y, start_y + board_h - 1)
                x = random.randint(start_x, start_x + board_w - 1)
                if (y, x) not in snake:
                    return y, x

        food = spawn_food()
        score = 0

        while True:
            key = stdscr.getch()

            if key in (ord('q'), ord('Q')):
                return  # quit the game entirely

            if key in (ord('r'), ord('R')):
                break  # restart the round

            if key in dirs:
                dy, dx = dirs[key]
                # Prevent reversing directly into yourself.
                if (dy, dx) != (-direction[0], -direction[1]):
                    next_direction = (dy, dx)

            direction = next_direction
            head = snake[0]
            new_head = (head[0] + direction[0], head[1] + direction[1])

            # Respawn food if it was eaten.
            ate = (new_head == food)

            # Check collisions.
            hit_wall = not (start_y <= new_head[0] < start_y + board_h
                            and start_x <= new_head[1] < start_x + board_w)
            hit_self = new_head in snake[:-1] if not ate else new_head in snake[:-2]

            if hit_wall or hit_self:
                stdscr.timeout(-1)
                stdscr.clear()
                make_border(stdscr, height, width, 0)
                msg = f"GAME OVER — final score: {score}"
                draw_text(stdscr, height // 2 - 1,
                          (width - len(msg)) // 2, msg, curses.color_pair(4))
                draw_text(stdscr, height // 2 + 1,
                          (width - len(HELP)) // 2, HELP, curses.A_DIM)
                stdscr.refresh()
                while True:
                    k = stdscr.getch()
                    if k in (ord('r'), ord('R')):
                        break
                    if k in (ord('q'), ord('Q')):
                        return
                break

            snake.insert(0, new_head)
            if ate:
                score += 1
                food = spawn_food()
            else:
                snake.pop()

            # Render.
            stdscr.clear()
            make_border(stdscr, height, width, 0)
            for i, (y, x) in enumerate(snake):
                attr = curses.color_pair(1 if i == 0 else 2)
                draw_text(stdscr, y, x, "@" if i == 0 else "o", attr)
            draw_text(stdscr, food[0], food[1], "*", curses.color_pair(3))
            label = f"Score: {score}   (Quit: Q / Restart: R)"
            draw_text(stdscr, 0, 2, label, curses.color_pair(4))
            stdscr.refresh()


def main():
    try:
        curses.wrapper(run)
    except KeyboardInterrupt:
        pass
    finally:
        print("\nThanks for playing! 👋")


if __name__ == "__main__":
    sys.exit(main())
