#!/usr/bin/env python3
"""ASCII Aquarium - A terminal screensaver with swimming fish, bubbles, and seaweed."""

import random
import time
import os
import signal
import sys
import math

FISH_RIGHT = [
    "><))°>",
    ">º)))>",
    ">=)))>",
    "><>))",
    ">=ºº>",
]

FISH_LEFT = [
    "<°((><",
    "<(((º<",
    "<(((=<",
    "((><>",
    "<ºº=<",
]

COLORS = [
    "\033[91m",
    "\033[93m",
    "\033[92m",
    "\033[96m",
    "\033[94m",
    "\033[95m",
    "\033[33m",
    "\033[36m",
]

RESET = "\033[0m"
BOLD = "\033[1m"


class Fish:
    def __init__(self, width, height):
        self.x = random.randint(0, width - 10)
        self.y = random.randint(2, height - 3)
        self.speed = random.uniform(0.3, 1.2)
        self.direction = random.choice([-1, 1])
        self.color = random.choice(COLORS)
        idx = random.randint(0, len(FISH_RIGHT) - 1)
        self.shape_right = FISH_RIGHT[idx]
        self.shape_left = FISH_LEFT[idx]
        self.wiggle = 0

    def move(self, width, height):
        self.x += self.speed * self.direction
        self.wiggle = (self.wiggle + 1) % 6
        if self.x > width - 8:
            self.direction = -1
        elif self.x < 0:
            self.direction = 1
        if random.random() < 0.05:
            self.y += random.choice([-1, 0, 1])
            self.y = max(2, min(height - 3, self.y))

    def draw(self):
        shape = self.shape_right if self.direction > 0 else self.shape_left
        y_offset = int(self.wiggle < 3)
        return int(self.x), self.y + y_offset, self.color + shape + RESET


class Bubble:
    def __init__(self, width, height):
        self.x = random.randint(2, width - 3)
        self.y = height - 2
        self.speed = random.uniform(0.4, 1.2)
        self.wobble = random.uniform(0, 6.28)
        self.size = random.choice(["o", "O", "°", "·"])

    def move(self):
        self.y -= self.speed
        self.wobble += 0.3
        self.x += math.sin(self.wobble) * 0.3

    def is_alive(self):
        return self.y > 0

    def draw(self):
        return int(self.x), int(self.y), "\033[96m" + self.size + RESET


class Seaweed:
    def __init__(self, x, height):
        self.x = x
        self.tall = random.randint(3, 7)
        self.phase = random.uniform(0, 6.28)

    def draw(self, ground_y, tick):
        segments = []
        for i in range(self.tall):
            sway = int(math.sin(tick * 0.08 + self.phase + i * 0.5) * 1.5)
            y = ground_y - 1 - i
            char = "|" if i < self.tall - 1 else "f"
            segments.append((self.x + sway, y, "\033[32m" + char + RESET))
        return segments


class TreasureChest:
    def __init__(self, width, height):
        self.x = random.randint(4, width - 8)
        self.y = height - 2
        self.open_timer = 0

    def draw(self, tick):
        if (tick % 120) < 60:
            return self.x, self.y, "\033[33m[__]{o}\033[0m"
        else:
            return self.x, self.y, "\033[33m[__]{ } \033[0m"


class Aquarium:
    def __init__(self):
        self.width, self.height = self.get_size()
        self.fishes = [Fish(self.width, self.height) for _ in range(10)]
        self.bubbles = []
        num_weed = min(8, max(2, self.width // 15))
        weed_positions = random.sample(range(2, self.width - 2), min(num_weed, self.width - 4))
        self.seaweeds = [Seaweed(x, self.height) for x in weed_positions]
        self.chest = TreasureChest(self.width, self.height)
        self.tick = 0

    def get_size(self):
        try:
            s = os.get_terminal_size()
            return s.columns, s.lines
        except Exception:
            return 80, 24

    def clear(self):
        sys.stdout.write("\033[2J\033[H")

    def mv(self, x, y):
        sys.stdout.write(f"\033[{y+1};{x+1}H")

    def water_bg(self):
        cycle = (self.tick % 600) / 600.0
        if cycle < 0.5:
            return "\033[44m"
        else:
            return "\033[48;5;17m"

    def spawn_bubble(self):
        if len(self.bubbles) < 12 and random.random() < 0.25:
            self.bubbles.append(Bubble(self.width, self.height))

    def render(self):
        self.clear()
        bg = self.water_bg()
        sys.stdout.write(bg)

        # Draw water surface
        self.mv(0, 0)
        wave = ""
        for i in range(self.width):
            if (i + self.tick // 3) % 4 < 2:
                wave += "~"
            else:
                wave += "-"
        sys.stdout.write("\033[96m" + wave + RESET + bg)

        # Draw sandy bottom
        self.mv(0, self.height - 1)
        sys.stdout.write("\033[33m" + "▒" * self.width + RESET)

        # Draw seaweed
        for weed in self.seaweeds:
            for x, y, ch in weed.draw(self.height - 1, self.tick):
                if 1 <= x < self.width - 1 and 1 <= y < self.height - 1:
                    self.mv(x, y)
                    sys.stdout.write(ch + bg)

        # Draw treasure chest
        cx, cy, cch = self.chest.draw(self.tick)
        self.mv(cx, cy)
        sys.stdout.write(cch + bg)

        # Draw bubbles
        for b in self.bubbles:
            bx, by, bch = b.draw()
            if 1 <= bx < self.width - 1 and 1 <= by < self.height - 1:
                self.mv(bx, by)
                sys.stdout.write(bch + bg)

        # Draw fish
        for f in self.fishes:
            fx, fy, fch = f.draw()
            if 1 <= fx < self.width - 8 and 1 <= fy < self.height - 2:
                self.mv(fx, fy)
                sys.stdout.write(fch + bg)

        # Title bar
        self.mv(0, 0)
        title = BOLD + " 🐠 ASCII Aquarium 🐠  " + RESET + bg
        sys.stdout.write(title)

        # Fish counter
        counter = f"  fish: {len(self.fishes)}  bubbles: {len(self.bubbles)} "
        self.mv(self.width - len(counter) - 1, 0)
        sys.stdout.write("\033[97m" + counter + RESET + bg)

        sys.stdout.write(RESET)
        sys.stdout.flush()

    def update(self):
        self.tick += 1
        for f in self.fishes:
            f.move(self.width, self.height)
        self.spawn_bubble()
        for b in self.bubbles:
            b.move()
        self.bubbles = [b for b in self.bubbles if b.is_alive()]

        # Check resize
        nw, nh = self.get_size()
        if (nw, nh) != (self.width, self.height):
            self.width, self.height = nw, nh

    def run(self):
        sys.stdout.write("\033[?25l")
        try:
            while True:
                self.update()
                self.render()
                time.sleep(0.08)
        except KeyboardInterrupt:
            pass
        finally:
            sys.stdout.write("\033[?25h" + RESET + "\033[49m")
            self.clear()
            print("🐟 Thanks for visiting the aquarium! 🐟")


def shutdown(signum, frame):
    sys.stdout.write("\033[?25h" + RESET + "\033[49m")
    sys.stdout.write("\033[2J\033[H")
    print("🐟 Thanks for visiting the aquarium! 🐟")
    sys.exit(0)


signal.signal(signal.SIGINT, shutdown)

if __name__ == "__main__":
    aq = Aquarium()
    aq.run()
