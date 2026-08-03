#!/usr/bin/env python3
"""terminal-typer: a small, no-dependency terminal typing game.

Words fall from the top of the terminal; type the frontmost word that
matches your buffer to clear it and score points. Ctrl-C to quit.
"""
import itertools
import random
import shutil
import sys
import time

WORDS = [
    "apple", "brave", "crisp", "dance", "eager", "flame", "globe", "haste",
    "ivory", "jolly", "knack", "lunar", "marsh", "neon", "ounce", "plush",
    "quilt", "rusty", "sable", "tulip", "ultra", "vivid", "waltz", "yield",
    "zesty", "amber", "bliss", "candy", "drift", "ember", "frost", "grain",
    "hover", "jumpy", "kiosk", "lodge", "mirth", "north", "olive", "pearl",
    "quack", "raven", "snowy", "trail", "under", "vapor", "wreath", "yeast",
]

MARGIN = "  "


class Colors:
    RESET = "\033[0m"
    RED = "\033[91m"
    GREEN = "\033[92m"
    CYAN = "\033[96m"
    DIM = "\033[2m"


def clear():
    sys.stdout.write("\033[2J\033[H")
    sys.stdout.flush()


def colorize(expected, typed):
    """Color each typed char green if correct, red if wrong; pad untyped."""
    out = []
    for expect, got in itertools.zip_longest(expected, typed):
        if got is None:
            out.append(expect)
        elif expect == got:
            out.append(f"{Colors.GREEN}{got}{Colors.RESET}")
        else:
            out.append(f"{Colors.RED}{got}{Colors.RESET}")
    return "".join(out)


def new_word(width, min_speed, max_speed):
    word = random.choice(WORDS)
    x = random.randint(0, max(0, width - len(word) - 2))
    return {"word": word, "x": x, "y": 0.0,
            "speed": random.uniform(min_speed, max_speed)}


def main():
    width, height = 50, 18
    try:
        cols, rows = shutil.get_terminal_size()
        width, height = cols, rows
    except Exception:
        pass
    height = max(height, 12)
    width = max(width, 40)

    import termios
    import tty
    from select import select

    fd = sys.stdin.fileno()
    old = termios.tcgetattr(fd)
    try:
        tty.setraw(fd)
        _play(fd, old, width, height, select)
    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, old)
        clear()
        sys.stdout.write(f"{Colors.RESET}goodbye!\n")


def _play(fd, old, width, height, select):
    arena_h = height - 6
    words = []
    buffer = ""
    score = 0
    typed_chars = 0
    start = time.monotonic()
    min_speed, max_speed = 0.15, 0.45
    spawn_every = 1.2
    last_spawn = time.monotonic()

    while True:
        now = time.monotonic()
        elapsed = now - start

        if now - last_spawn > spawn_every:
            words.append(new_word(width, min_speed, max_speed))
            last_spawn = now
            spawn_every = max(0.35, 1.2 - elapsed / 90.0)
            min_speed = min(0.6, min_speed + 0.005)
            max_speed = min(1.0, max_speed + 0.005)

        while True:
            ready, _, _ = select([fd], [], [], 0)
            if not ready:
                break
            ch = sys.stdin.read(1)
            if ch == "\x03":
                return
            if ch == "\x7f":
                buffer = buffer[:-1]
            elif ch in ("\r", "\n"):
                buffer = ""
            elif ch.isprintable():
                buffer += ch
                typed_chars += 1

        for w in list(words):
            w["y"] += w["speed"]
            if w["y"] > arena_h:
                words.remove(w)

        alive = [w for w in words if w["word"].startswith(buffer) and buffer]
        if alive:
            target = min(alive, key=lambda w: w["y"])
            if buffer == target["word"]:
                words.remove(target)
                score += len(target["word"]) + 10
                buffer = ""
        elif buffer and not any(w["word"].startswith(buffer) for w in words):
            buffer = ""

        _render(words, buffer, score, elapsed, typed_chars, width, arena_h)
        time.sleep(0.05)


def _render(words, buffer, score, elapsed, typed_chars, width, arena_h):
    clear()
    grid = [[" "] * width for _ in range(arena_h)]
    for w in words:
        y = int(w["y"])
        if 0 <= y < arena_h:
            for i, ch in enumerate(w["word"]):
                x = w["x"] + i
                if 0 <= x < width:
                    grid[y][x] = ch
    for row in grid:
        print(MARGIN + "".join(row))

    print(MARGIN + "-" * width)
    wpm = int(typed_chars / 5.0 / max(elapsed / 60.0, 1e-6))
    header = (
        f"{Colors.CYAN}score: {score}{Colors.RESET}   "
        f"wpm: {wpm}   "
        f"secs: {elapsed:.0f}   "
        f"{Colors.DIM}(Ctrl-C to quit){Colors.RESET}"
    )
    print(header)
    print(MARGIN + "type: " + colorize(buffer, buffer))


if __name__ == "__main__":
    main()
