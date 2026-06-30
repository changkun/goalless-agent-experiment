#!/usr/bin/env python3
"""
Terminal rain — falling digits where primes glow differently.
Press Ctrl+C to exit. Resize your terminal freely.
"""

import random
import time
import sys
import os
import signal
import math

ESC = "\033["

def term_size():
    try:
        cols, rows = os.get_terminal_size()
    except OSError:
        cols, rows = 80, 24
    return cols, rows

def is_prime(n):
    if n < 2: return False
    if n < 4: return True
    if n % 2 == 0 or n % 3 == 0: return False
    i = 5
    while i * i <= n:
        if n % i == 0 or n % (i + 2) == 0: return False
        i += 6
    return True

# ANSI helpers
def move(r, c): return f"{ESC}{r};{c}H"
def green(s):   return f"{ESC}32m{s}{ESC}0m"
def bright_green(s): return f"{ESC}92m{s}{ESC}0m"
def cyan(s):    return f"{ESC}96m{s}{ESC}0m"
def white(s):   return f"{ESC}97m{s}{ESC}0m"
def dim(s):     return f"{ESC}2m{s}{ESC}0m"
def yellow(s):  return f"{ESC}93m{s}{ESC}0m"
def hide_cursor(): return f"{ESC}?25l"
def show_cursor(): return f"{ESC}?25h"
def clear(): return f"{ESC}2J{ESC}H"

CHARS = "0123456789"

class Drop:
    __slots__ = ("col", "row", "speed", "length", "tail", "value")

    def __init__(self, col, rows):
        self.col = col
        self.row = random.randint(-rows, 0)
        self.speed = random.choice([1, 1, 1, 2])
        self.length = random.randint(4, 20)
        self.tail = []
        self.value = random.randint(0, 999)

    def tick(self, rows):
        self.row += self.speed
        self.value = (self.value * 6364136223846793005 + 1) & 0xFFFF  # fast lcg
        ch = CHARS[self.value % len(CHARS)]
        self.tail.insert(0, (self.row, ch))
        if len(self.tail) > self.length:
            self.tail.pop()
        return self.row - self.length > rows  # done when fully off screen


def render(drops, cols, rows, prime_count, frame):
    buf = []
    for drop in drops:
        for i, (r, ch) in enumerate(drop.tail):
            if 1 <= r <= rows:
                num = int(ch)
                if i == 0:
                    # Head — bright white or cyan for primes
                    styled = cyan(ch) if is_prime(num) else white(ch)
                elif i < 3:
                    styled = bright_green(ch)
                elif i < 8:
                    styled = green(ch)
                else:
                    styled = dim(green(ch))
                buf.append(f"{move(r, drop.col)}{styled}")

    # Status bar
    elapsed = frame / 20
    minutes = int(elapsed // 60)
    seconds = int(elapsed % 60)
    status = f" primes seen: {yellow(str(prime_count))}  |  time: {green(f'{minutes:02d}:{seconds:02d}')}  |  drops: {green(str(len(drops)))}  "
    padded = status.ljust(cols)
    buf.append(f"{move(rows, 1)}{ESC}7m{padded[:cols]}{ESC}0m")

    sys.stdout.write("".join(buf))
    sys.stdout.flush()


def main():
    cols, rows = term_size()
    sys.stdout.write(hide_cursor() + clear())
    sys.stdout.flush()

    drops = [Drop(c, rows) for c in range(1, cols + 1) if random.random() < 0.3]
    prime_count = 0
    frame = 0
    prime_seen = set()

    def on_resize(sig, frame_):
        nonlocal cols, rows, drops
        cols, rows = term_size()
        sys.stdout.write(clear())
        drops = [d for d in drops if d.col <= cols]

    signal.signal(signal.SIGWINCH, on_resize)

    try:
        while True:
            # Spawn new drops randomly
            if random.random() < 0.4:
                c = random.randint(1, cols)
                drops.append(Drop(c, rows))

            # Count primes in current heads
            for drop in drops:
                if drop.tail:
                    ch = drop.tail[0][1]
                    num_val = drop.value
                    if is_prime(num_val % 1000) and num_val not in prime_seen:
                        prime_seen.add(num_val)
                        prime_count += 1

            # Keep set from growing unboundedly
            if len(prime_seen) > 5000:
                prime_seen.clear()

            render(drops, cols, rows, prime_count, frame)

            # Remove finished drops
            drops = [d for d in drops if not d.tick(rows)]

            frame += 1
            time.sleep(0.05)

    except KeyboardInterrupt:
        pass
    finally:
        sys.stdout.write(show_cursor() + clear())
        sys.stdout.flush()
        print(f"Rain stopped. Primes encountered: {prime_count}")


if __name__ == "__main__":
    main()
