#!/usr/bin/env python3
"""Mini Dungeon Crawler - a tiny terminal roguelike."""
import os
import random
import sys

W, H = 21, 11
WALL, FLOOR, STAIRS = "#", ".", ">"
TILES = {WALL: "\033[90m#\033[0m", FLOOR: ".", STAIRS: "\033[33m>\033[0m"}

MOVES = {
    "w": (0, -1), "a": (-1, 0), "s": (0, 1), "d": (1, 0),
    "up": (0, -1), "left": (-1, 0), "down": (0, 1), "right": (1, 0),
}
KEYMAP = {
    "\x1b[A": "up", "\x1b[B": "down",
    "\x1b[C": "right", "\x1b[D": "left",
}
HELP = "\n".join([
    "Controls:", "  w/a/s/d or arrows  move",
    "  e                   attack adjacent enemy",
    "  i                   inventory",
    "  h                   this help",
    "  q                   quit",
])


def build_dungeon():
    grid = [[WALL] * W for _ in range(H)]
    # carve a simple interior
    for y in range(1, H - 1):
        for x in range(1, W - 1):
            grid[y][x] = FLOOR
    # a few wall pillars for interest
    for px, py in [(7, 3), (13, 3), (7, 7), (13, 7), (10, 5)]:
        grid[py][px] = WALL
    grid[1][1] = STAIRS
    return grid


def neighbors(x, y):
    for dx, dy in MOVES.values():
        yield x + dx, y + dy


class Game:
    def __init__(self):
        self.grid = build_dungeon()
        self.px, self.py = W - 2, H - 2  # player start (bottom-right)
        self.hp, self.maxhp = 15, 15
        self.gold = 0
        self.turns = 0
        self.enemies = []
        # place 3 goblins away from the player
        spawns = [(x, y) for x in range(1, W - 1) for y in range(1, H - 1)
                  if self.grid[y][x] == FLOOR and (x, y) != (self.px, self.py)
                  and self.grid[y][x] != STAIRS and (x, y) not in [(7, 3), (13, 3), (7, 7), (13, 7), (10, 5)]]
        random.shuffle(spawns)
        for x, y in spawns[:3]:
            self.enemies.append({"x": x, "y": y, "hp": 4, "dmg": 2})
        self.gold_x, self.gold_y = spawns[8] if len(spawns) > 8 else (W // 2, H // 2)

    def tile(self, x, y):
        if (x, y) == (self.px, self.py):
            return "\033[36m@\033[0m"
        if (x, y) == (self.gold_x, self.gold_y):
            return "\033[33m$\033[0m"
        for e in self.enemies:
            if (e["x"], e["y"]) == (x, y):
                return "\033[31mG\033[0m"
        return TILES[self.grid[y][x]]

    def render(self, msg=""):
        os.system("clear")
        print("=" * (W + 4))
        for y in range(H):
            print("| " + "".join(self.tile(x, y) for x in range(W)) + " |")
        print("=" * (W + 4))
        print(f"HP {self.hp}/{self.maxhp}  Gold {self.gold}  Turns {self.turns}"
              f"  [(x,y) ({self.px},{self.py})]")
        print(msg)

    def move(self, cmd):
        dx, dy = MOVES[cmd]
        nx, ny = self.px + dx, self.py + dy
        if not (0 <= nx < W and 0 <= ny < H):
            return "You bump the edge of the dungeon."
        if self.grid[ny][nx] == WALL:
            return "A wall blocks your way."
        if any((e["x"], e["y"]) == (nx, ny) for e in self.enemies):
            return "A goblin is in the way — attack it with [e]."
        self.px, self.py = nx, ny
        self.turns += 1
        if (nx, ny) == (self.gold_x, self.gold_y):
            self.gold += 5
            self.gold_x, self.gold_y = -1, -1
            return "You found 5 gold!"
        if self.grid[ny][nx] == STAIRS:
            return "VICTORY! You reached the stairs."
        return ""

    def attack(self):
        for e in self.enemies:
            if (e["x"], e["y"]) in neighbors(self.px, self.py):
                e["hp"] -= 4
                if e["hp"] <= 0:
                    self.enemies.remove(e)
                    return f"You slay a goblin! +2 gold"
                return f"Goblin hit ({e['hp']} hp left)."
        return "Nothing to attack nearby."

    def enemy_turn(self):
        if not self.enemies:
            return
        px, py = self.px, self.py
        for e in self.enemies:
            if abs(e["x"] - px) + abs(e["y"] - py) == 1:
                self.hp -= e["dmg"]
                return f"A goblin hits you for {e['dmg']}. ({self.hp} hp)"
        # simple pursuit: move one step closer
        e = self.enemies[0]
        ex, ey = e["x"], e["y"]
        if ex != px:
            ex += 1 if px > ex else -1
        elif ey != py:
            ey += 1 if py > ey else -1
        if (ex, ey) != (px, py) and self.grid[ey][ex] != WALL \
                and (ex, ey) != (self.gold_x, self.gold_y):
            e["x"], e["y"] = ex, ey
        return ""

    def inventory(self):
        return "".join([
            "You're the proud owner of:",
            f"  HP {self.hp}/{self.maxhp}",
            f"  Gold {self.gold}",
            f"  Turns {self.turns}",
        ])


def get_key():
    ch = sys.stdin.read(1)
    if not ch:
        sys.exit(0)
    if ch == "\x1b":
        seq = sys.stdin.read(2)
        return KEYMAP.get("\x1b" + seq, "?")
    return ch.lower()


def main():
    g = Game()
    msg = "Welcome! Find the stairs [>]. [h] for help."
    while True:
        g.render(msg)
        if g.hp <= 0:
            print("\033[31mYou have died.\033[0m")
            print("Try again: python3 dungeon.py")
            break
        if g.px == 1 and g.py == 1:
            print("\033[32mCongratulations, you escaped the dungeon!\033[0m")
            print(f"Gold: {g.gold}  Turns: {g.turns}")
            break
        key = get_key()
        if key == "q":
            print("Goodbye!")
            break
        if key == "h":
            msg = HELP
            continue
        if key == "i":
            msg = g.inventory()
            continue
        if key == "e":
            msg = g.attack() + (" " + g.enemy_turn() if g.enemies else "")
            continue
        if key in MOVES:
            r = g.move(key)
            msg = r
            if g.enemies:
                et = g.enemy_turn()
                if et:
                    msg = (r + "  " if r else "") + et
            continue
        msg = "Unknown command."


if __name__ == "__main__":
    main()
