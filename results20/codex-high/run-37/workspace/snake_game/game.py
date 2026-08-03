"""Terminal Snake game using only the Python standard library."""

import curses
import random
import time
from pathlib import Path

WIDTH, HEIGHT = 40, 20
SCORE_FILE = Path(__file__).parent / "highscores.txt"

PAIRS = {
    "board": (0, 0),
    "snake_head": (1, 4),
    "snake_tail": (2, 4),
    "food": (3, 3),
    "text": (4, 7),
}

DIRS = {
    curses.KEY_UP: (0, -1),
    curses.KEY_DOWN: (0, 1),
    curses.KEY_LEFT: (-1, 0),
    curses.KEY_RIGHT: (1, 0),
}


def load_scores():
    scores = []
    if SCORE_FILE.exists():
        for line in SCORE_FILE.read_text().splitlines():
            if ":" in line:
                name, value = line.strip().rsplit(":", 1)
                try:
                    scores.append((name.strip(), int(value)))
                except ValueError:
                    continue
    return scores


def save_scores(scores):
    SCORE_FILE.write_text("\n".join(f"{name}: {value}" for name, value in scores) + "\n")


def draw_scores(scr):
    scr.clear()
    title = "HIGH SCORES"
    x = (WIDTH + 2 - len(title)) // 2
    scr.addstr(1, x, title, curses.color_pair(PAIRS["text"]) | curses.A_BOLD)
    scores = sorted(load_scores(), key=lambda s: s[1], reverse=True)[:10]
    if not scores:
        scr.addstr(4, x, "No scores yet. Play a round!", curses.color_pair(PAIRS["text"]))
    for i, (name, value) in enumerate(scores, start=1):
        line = f"{i:>2}. {name:<16} {value:>5}"
        scr.addstr(3 + i, x - 4, line, curses.color_pair(PAIRS["text"]))
    prompt = "Press any key to continue"
    scr.addstr(HEIGHT + 2, (WIDTH + 2 - len(prompt)) // 2, prompt, curses.color_pair(PAIRS["text"]))
    scr.refresh()
    scr.getch()


def play(scr, name):
    curses.curs_set(0)
    scr.nodelay(True)
    scr.timeout(150)

    # Border
    scr.attrset(curses.color_pair(PAIRS["board"]))
    scr.border()

    snake = [(WIDTH // 2, HEIGHT // 2)]
    direction = (1, 0)
    food = _random_food(snake)
    score = 0
    speed = 150

    while True:
        key = scr.getch()
        if key in (curses.KEY_UP, curses.KEY_DOWN, curses.KEY_LEFT, curses.KEY_RIGHT):
            new_dir = DIRS[key]
            # prevent reversing into itself
            if (new_dir[0], new_dir[1]) != (-direction[0], -direction[1]):
                direction = new_dir
        elif key in (ord("q"), ord("Q")):
            return None

        head = (snake[0][0] + direction[0], snake[0][1] + direction[1])
        hit_wall = not (1 <= head[0] < WIDTH + 1 and 1 <= head[1] < HEIGHT + 1)
        if hit_wall or head in snake:
            break

        snake.insert(0, head)
        scr.addch(head[1], head[0], "#", curses.color_pair(PAIRS["snake_head"]))

        if head == food:
            score += 1
            speed = max(50, 150 - score * 4)
            scr.timeout(speed)
            food = place_food()
            scr.addch(food[1], food[0], "@", curses.color_pair(PAIRS["food"]))
        else:
            tail = snake.pop()
            scr.addch(tail[1], tail[0], " ", curses.color_pair(PAIRS["board"]))

        scr.addstr(0, 2, f"SCORE: {score}", curses.color_pair(PAIRS["text"]))
        scr.refresh()

    # Game over
    if score > 0:
        scores = load_scores()
        scores.append((name, score))
        save_scores(sorted(scores, key=lambda s: s[1], reverse=True)[:10])

    _game_over(scr, score)
    return score


def _game_over(scr, score):
    scr.timeout(-1)
    scr.nodelay(False)
    scr.clear()
    msg = "GAME OVER"
    x = (WIDTH + 2 - len(msg)) // 2
    scr.addstr(HEIGHT // 2 - 1, x, msg, curses.color_pair(PAIRS["text"]) | curses.A_BOLD)
    line = f"Your score: {score}"
    scr.addstr(HEIGHT // 2, x - 4, line, curses.color_pair(PAIRS["text"]))
    prompt = "Press any key to return to menu"
    scr.addstr(HEIGHT // 2 + 2, (WIDTH + 2 - len(prompt)) // 2, prompt, curses.color_pair(PAIRS["text"]))
    scr.refresh()
    scr.getch()


def _random_food(snake):
    free = [(x, y) for y in range(1, HEIGHT + 1) for x in range(1, WIDTH + 1) if (x, y) not in snake]
    return random.choice(free)


def run(stdscr):
    curses.curs_set(0)
    curses.start_color()
    for idx, (fg, bg) in enumerate(
        [(curses.COLOR_BLACK, curses.COLOR_WHITE),      # board
         (curses.COLOR_CYAN, curses.COLOR_WHITE),       # snake head
         (curses.COLOR_GREEN, curses.COLOR_WHITE),      # snake tail
         (curses.COLOR_RED, curses.COLOR_WHITE),        # food
         (curses.COLOR_MAGENTA, curses.COLOR_WHITE)],   # text
        start=1,
    ):
        curses.init_pair(idx, fg, bg)

    while True:
        scr.clear()
        title = "SNAKE"
        x = (WIDTH + 2 - len(title)) // 2
        scr.addstr(1, x, title, curses.color_pair(PAIRS["text"]) | curses.A_BOLD)

        menu = [
            ("[P]lay", 3),
            ("[H]igh scores", 4),
            ("[Q]uit", 5),
        ]
        for text, row in menu:
            scr.addstr(row, (WIDTH + 2 - len(text)) // 2, text, curses.color_pair(PAIRS["text"]))

        scr.refresh()
        key = scr.getch()
        if key in (ord("p"), ord("P")):
            name = _prompt_name(scr)
            if name is not None:
                play(scr, name)
        elif key in (ord("h"), ord("H")):
            draw_scores(scr)
        elif key in (ord("q"), ord("Q")):
            break


def _prompt_name(scr):
    scr.clear()
    msg = "Enter your name: "
    scr.addstr(HEIGHT // 2 - 1, 1, msg, curses.color_pair(PAIRS["text"]))
    scr.refresh()
    curses.echo()
    curses.curs_set(1)
    try:
        name = scr.getstr(HEIGHT // 2 - 1, len(msg) + 1, 20).decode().strip()
    finally:
        curses.noecho()
        curses.curs_set(0)
    return name or "Player"


def main():
    curses.wrapper(run)


if __name__ == "__main__":
    main()
