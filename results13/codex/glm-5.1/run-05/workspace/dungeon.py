#!/usr/bin/env python3
"""
🗡️  DUNGEON CRAWLER — A terminal roguelike
Navigate procedurally generated dungeons, fight monsters, collect loot, find the exit.
"""

import random
import sys
import os
import time

# ── Config ──────────────────────────────────────────────────────────
DUNGEON_W, DUNGEON_H = 50, 20
FOV_RADIUS = 4
ROOM_MIN, ROOM_MAX = 3, 8
ROOM_ATTEMPTS = 18

# ── Tile types ──────────────────────────────────────────────────────
WALL = 0
FLOOR = 1
DOOR = 2
STAIRS_DOWN = 3
STAIRS_UP = 4

TILE_CHAR = {
    WALL: "█",
    FLOOR: "·",
    DOOR: "+",
    STAIRS_DOWN: "▼",
    STAIRS_UP: "▲",
}

# ── Monsters ────────────────────────────────────────────────────────
MONSTER_TABLE = [
    {"name": "Rat",         "hp": 3,  "atk": 1, "def": 0, "xp": 2,  "color": "\033[38;5;130m"},
    {"name": "Goblin",      "hp": 6,  "atk": 2, "def": 1, "xp": 5,  "color": "\033[38;5;2m"},
    {"name": "Skeleton",    "hp": 8,  "atk": 3, "def": 2, "xp": 8,  "color": "\033[38;5;248m"},
    {"name": "Orc",         "hp": 12, "atk": 4, "def": 3, "xp": 12, "color": "\033[38;5;28m"},
    {"name": "Dark Mage",   "hp": 10, "atk": 6, "def": 1, "xp": 15, "color": "\033[38;5;93m"},
    {"name": "Dragon",      "hp": 25, "atk": 8, "def": 5, "xp": 30, "color": "\033[38;5;196m"},
]

# ── Items ───────────────────────────────────────────────────────────
ITEM_TABLE = [
    {"name": "Health Potion", "type": "potion", "value": 8,  "char": "!", "color": "\033[38;5;196m"},
    {"name": "Strength Scroll","type": "scroll", "value": 3,  "char": "?", "color": "\033[38;5;220m"},
    {"name": "Iron Sword",    "type": "weapon", "value": 3,  "char": "/", "color": "\033[38;5;248m"},
    {"name": "Steel Sword",   "type": "weapon", "value": 5,  "char": "/", "color": "\033[38;5;252m"},
    {"name": "Leather Armor", "type": "armor",  "value": 2,  "char": "[", "color": "\033[38;5;130m"},
    {"name": "Chain Mail",    "type": "armor",  "value": 4,  "char": "[", "color": "\033[38;5;248m"},
    {"name": "Gold",          "type": "gold",   "value": 0,  "char": "$", "color": "\033[38;5;220m"},
]

# ── Dungeon generation ──────────────────────────────────────────────
class Room:
    def __init__(self, x, y, w, h):
        self.x, self.y, self.w, self.h = x, y, w, h

    @property
    def center(self):
        return self.x + self.w // 2, self.y + self.h // 2

    def intersects(self, other, margin=1):
        return (
            self.x - margin < other.x + other.w + margin
            and self.x + self.w + margin > other.x - margin
            and self.y - margin < other.y + other.h + margin
            and self.y + self.h + margin > other.y - margin
        )

    def random_tile(self):
        return random.randint(self.x, self.x + self.w - 1), random.randint(self.y, self.y + self.h - 1)


def generate_dungeon(level):
    grid = [[WALL] * DUNGEON_W for _ in range(DUNGEON_H)]
    rooms = []

    for _ in range(ROOM_ATTEMPTS):
        w = random.randint(ROOM_MIN, ROOM_MAX)
        h = random.randint(ROOM_MIN, ROOM_MAX)
        x = random.randint(1, DUNGEON_W - w - 1)
        y = random.randint(1, DUNGEON_H - h - 1)
        candidate = Room(x, y, w, h)
        if any(candidate.intersects(r) for r in rooms):
            continue
        rooms.append(candidate)
        for ry in range(y, y + h):
            for rx in range(x, x + w):
                grid[ry][rx] = FLOOR

    # Connect rooms with corridors
    for i in range(1, len(rooms)):
        ax, ay = rooms[i - 1].center
        bx, by = rooms[i].center
        # L-shaped corridor
        if random.random() < 0.5:
            carve_h(grid, ay, ax, bx)
            carve_v(grid, ax, by, ay)
        else:
            carve_v(grid, ax, by, ay)
            carve_h(grid, ay, ax, bx)

    # Place doors at corridor/room boundaries
    for room in rooms:
        for ry in range(room.y, room.y + room.h):
            for rx in range(room.x, room.x + room.w):
                for dy, dx in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                    ny, nx = ry + dy, rx + dx
                    if 0 <= ny < DUNGEON_H and 0 <= nx < DUNGEON_W:
                        if grid[ny][nx] == FLOOR and (ny < room.y or ny >= room.y + room.h or nx < room.x or nx >= room.x + room.w):
                            grid[ny][nx] = DOOR

    # Stairs
    if len(rooms) >= 2:
        sx, sy = rooms[0].random_tile()
        grid[sy][sx] = STAIRS_UP
        ex, ey = rooms[-1].random_tile()
        grid[ey][ex] = STAIRS_DOWN

    return grid, rooms


def carve_h(grid, y, x1, x2):
    for x in range(min(x1, x2), max(x1, x2) + 1):
        if 0 <= y < DUNGEON_H and 0 <= x < DUNGEON_W:
            if grid[y][x] == WALL:
                grid[y][x] = FLOOR


def carve_v(grid, x, y1, y2):
    for y in range(min(y1, y2), max(y1, y2) + 1):
        if 0 <= y < DUNGEON_H and 0 <= x < DUNGEON_W:
            if grid[y][x] == WALL:
                grid[y][x] = FLOOR


# ── Entities ────────────────────────────────────────────────────────
class Player:
    def __init__(self, x, y):
        self.x, self.y = x, y
        self.hp = 20
        self.max_hp = 20
        self.atk = 2
        self.defense = 0
        self.xp = 0
        self.level = 1
        self.gold = 0
        self.weapon_bonus = 0
        self.armor_bonus = 0
        self.visible = set()
        self.explored = set()

    def attack_power(self):
        return self.atk + self.weapon_bonus

    def total_defense(self):
        return self.defense + self.armor_bonus

    def gain_xp(self, amount):
        self.xp += amount
        needed = self.level * 15
        while self.xp >= needed:
            self.xp -= needed
            self.level += 1
            self.max_hp += 5
            self.hp = min(self.hp + 5, self.max_hp)
            self.atk += 1
            needed = self.level * 15
            return True
        return False


class Monster:
    def __init__(self, x, y, template, level_scale):
        self.x, self.y = x, y
        self.name = template["name"]
        self.color = template["color"]
        scale = 1 + level_scale * 0.15
        self.hp = int(template["hp"] * scale)
        self.max_hp = self.hp
        self.atk = int(template["atk"] * scale)
        self.defense = template["def"]
        self.xp = int(template["xp"] * scale)
        self.char = self.name[0]


class Item:
    def __init__(self, x, y, template, gold_amount=0):
        self.x, self.y = x, y
        self.name = template["name"]
        self.item_type = template["type"]
        self.value = template["value"]
        self.char = template["char"]
        self.color = template["color"]
        if self.item_type == "gold":
            self.value = gold_amount or random.randint(5, 25 + 5)


# ── FOV ─────────────────────────────────────────────────────────────
def compute_fov(grid, px, py, radius):
    visible = set()
    for angle_step in range(360):
        angle = angle_step * (3.14159 / 180)
        dx = 0.0
        dy = 0.0
        for step in range(1, radius + 1):
            dx += 0.01745 * 57.2958  # ~1 tile
            # Ray casting per tile
            tx = px + int(round(step * (1 if angle_step % 2 == 0 else -1) * 0.5))
            ty = py + int(round(step * (1 if angle_step % 3 == 0 else -1) * 0.5))
        # Simpler: just use distance + Bresenham-ish
    # Actually, let's use a simple flood approach
    visible.add((px, py))
    for dy in range(-radius, radius + 1):
        for dx in range(-radius, radius + 1):
            nx, ny = px + dx, py + dy
            if 0 <= nx < DUNGEON_W and 0 <= ny < DUNGEON_H:
                if dx * dx + dy * dy <= radius * radius:
                    # Simple line-of-sight: walk tiles from player to target
                    if has_los(grid, px, py, nx, ny):
                        visible.add((nx, ny))
    return visible


def has_los(grid, x1, y1, x2, y2):
    dx = abs(x2 - x1)
    dy = abs(y2 - y1)
    sx = 1 if x1 < x2 else -1
    sy = 1 if y1 < y2 else -1
    err = dx - dy
    cx, cy = x1, y1
    while (cx, cy) != (x2, y2):
        if (cx, cy) != (x1, y1) and grid[cy][cx] == WALL:
            return False
        e2 = 2 * err
        if e2 > -dy:
            err -= dy
            cx += sx
        if e2 < dx:
            err += dx
            cy += sy
    return True


# ── Game state ──────────────────────────────────────────────────────
class Game:
    def __init__(self):
        self.level = 1
        self.messages = []
        self.log("Welcome, adventurer! Find the stairs ▼ to descend deeper.")
        self.log("Move: hjkl/yubn  |  Use potion: p  |  Wait: .  |  Quit: q")
        self.new_level(first=True)

    def new_level(self, first=False):
        self.grid, self.rooms = generate_dungeon(self.level)
        start_room = self.rooms[0] if self.rooms else None
        if start_room:
            sx, sy = start_room.center
        else:
            sx, sy = DUNGEON_W // 2, DUNGEON_H // 2

        if first:
            self.player = Player(sx, sy)
        else:
            self.player.x, self.player.y = sx, sy

        self.monsters = []
        self.items = []

        # Spawn monsters (more on deeper levels)
        for room in self.rooms[1:]:
            n_monsters = random.randint(0, min(3, 1 + self.level // 2))
            for _ in range(n_monsters):
                mx, my = room.random_tile()
                if self.grid[my][mx] in (FLOOR, DOOR):
                    tier = min(len(MONSTER_TABLE) - 1, random.randint(0, min(self.level + 1, len(MONSTER_TABLE) - 1)))
                    self.monsters.append(Monster(mx, my, MONSTER_TABLE[tier], self.level))

        # Spawn items
        for room in self.rooms[1:]:
            if random.random() < 0.6:
                ix, iy = room.random_tile()
                if self.grid[iy][ix] == FLOOR:
                    tier = random.randint(0, min(len(ITEM_TABLE) - 1, self.level))
                    self.items.append(Item(ix, iy, ITEM_TABLE[tier]))

        self.update_fov()
        self.log(f"─ You descend to level {self.level} ─")

    def log(self, msg):
        self.messages.append(msg)
        if len(self.messages) > 100:
            self.messages = self.messages[-100:]

    def update_fov(self):
        self.player.visible = compute_fov(self.grid, self.player.x, self.player.y, FOV_RADIUS)
        self.player.explored |= self.player.visible

    def monster_at(self, x, y):
        for m in self.monsters:
            if m.x == x and m.y == y and m.hp > 0:
                return m
        return None

    def item_at(self, x, y):
        for i in self.items:
            if i.x == x and i.y == y:
                return i
        return None

    def move_player(self, dx, dy):
        nx, ny = self.player.x + dx, self.player.y + dy
        if not (0 <= nx < DUNGEON_W and 0 <= ny < DUNGEON_H):
            return
        tile = self.grid[ny][nx]
        if tile == WALL:
            return

        monster = self.monster_at(nx, ny)
        if monster:
            self.attack_monster(monster)
            self.monster_turn()
            return

        self.player.x, self.player.y = nx, ny

        # Pick up items
        item = self.item_at(nx, ny)
        if item:
            self.pickup_item(item)

        # Stairs
        if tile == STAIRS_DOWN:
            self.level += 1
            self.log("You find stairs leading deeper...")
            self.new_level()
            return

        # Open doors
        if tile == DOOR:
            self.grid[ny][nx] = FLOOR

        self.update_fov()
        self.monster_turn()

    def attack_monster(self, m):
        dmg = max(1, self.player.attack_power() - m.defense + random.randint(-1, 1))
        m.hp -= dmg
        self.log(f"You hit {m.name} for {dmg} dmg!")
        if m.hp <= 0:
            self.log(f"{m.name} is slain! (+{m.xp}xp)")
            leveled = self.player.gain_xp(m.xp)
            if leveled:
                self.log(f"*** Level up! You are now level {self.player.level}! ***")
            self.monsters.remove(m)

    def pickup_item(self, item):
        if item.item_type == "potion":
            heal = item.value
            self.player.hp = min(self.player.max_hp, self.player.hp + heal)
            self.log(f"Used {item.name}! Healed {heal} HP.")
            self.items.remove(item)
        elif item.item_type == "scroll":
            self.player.atk += item.value
            self.log(f"Read {item.name}! Attack +{item.value}.")
            self.items.remove(item)
        elif item.item_type == "weapon":
            if item.value > self.player.weapon_bonus:
                self.log(f"Equipped {item.name}! Weapon +{item.value}.")
                self.player.weapon_bonus = item.value
            else:
                self.log(f"Picked up {item.name} but your weapon is better.")
            self.items.remove(item)
        elif item.item_type == "armor":
            if item.value > self.player.armor_bonus:
                self.log(f"Equipped {item.name}! Armor +{item.value}.")
                self.player.armor_bonus = item.value
            else:
                self.log(f"Picked up {item.name} but your armor is better.")
            self.items.remove(item)
        elif item.item_type == "gold":
            self.player.gold += item.value
            self.log(f"Picked up {item.value} gold!")
            self.items.remove(item)

    def use_potion_auto(self):
        # No inventory — potions are used on pickup. This is a "wait and heal" command
        if self.player.hp < self.player.max_hp:
            heal = min(2, self.player.max_hp - self.player.hp)
            self.player.hp += heal
            self.log(f"You rest briefly and recover {heal} HP.")
        else:
            self.log("You are at full health.")
        self.monster_turn()

    def monster_turn(self):
        for m in self.monsters:
            if m.hp <= 0:
                continue
            dist = abs(m.x - self.player.x) + abs(m.y - self.player.y)
            if dist <= FOV_RADIUS + 2 and (m.x, m.y) in self.player.visible:
                # Chase player
                dx = (1 if self.player.x > m.x else -1 if self.player.x < m.x else 0)
                dy = (1 if self.player.y > m.y else -1 if self.player.y < m.y else 0)
                # Prefer axis with larger distance
                if abs(self.player.x - m.x) >= abs(self.player.y - m.y):
                    nx, ny = m.x + dx, m.y
                else:
                    nx, ny = m.x, m.y + dy

                # Adjacent? Attack!
                if abs(m.x - self.player.x) + abs(m.y - self.player.y) == 1:
                    dmg = max(1, m.atk - self.player.total_defense() + random.randint(-1, 1))
                    self.player.hp -= dmg
                    self.log(f"{m.name} hits you for {dmg} dmg!")
                    if self.player.hp <= 0:
                        self.log("You have been slain...")
                        return
                elif 0 <= nx < DUNGEON_W and 0 <= ny < DUNGEON_H:
                    if self.grid[ny][nx] != WALL and not self.monster_at(nx, ny) and (nx, ny) != (self.player.x, self.player.y):
                        m.x, m.y = nx, ny

    def render(self):
        os.system("clear" if os.name != "nt" else "cls")
        R = "\033[0m"
        B = "\033[1m"
        DIM = "\033[2m"

        # Map
        lines = []
        for y in range(DUNGEON_H):
            row = ""
            for x in range(DUNGEON_W):
                if (x, y) in self.player.visible:
                    tile = self.grid[y][x]
                    # Monster?
                    m = self.monster_at(x, y)
                    if m:
                        row += f"{m.color}{m.char}{R}"
                    elif (x, y) == (self.player.x, self.player.y):
                        row += f"{B}\033[38;5;255m@{R}"
                    else:
                        # Item?
                        i = self.item_at(x, y)
                        if i:
                            row += f"{i.color}{i.char}{R}"
                        else:
                            ch = TILE_CHAR.get(tile, "?")
                            if tile == WALL:
                                row += f"{DIM}\033[38;5;240m{ch}{R}"
                            else:
                                row += f"\033[38;5;180m{ch}{R}"
                elif (x, y) in self.player.explored:
                    ch = TILE_CHAR.get(self.grid[y][x], "?")
                    row += f"{DIM}\033[38;5;235m{ch}{R}"
                else:
                    row += " "
            lines.append(row)

        print("\n".join(lines))

        # HUD
        p = self.player
        hp_bar = "█" * max(0, int(p.hp / p.max_hp * 20)) + "░" * max(0, 20 - int(p.hp / p.max_hp * 20))
        print(f"")
        print(f"  {B}HP{R} [{hp_bar}] {p.hp}/{p.max_hp}  "
              f"{B}ATK{R} {p.attack_power()}  {B}DEF{R} {p.total_defense()}  "
              f"{B}LVL{R} {p.level}  {B}XP{R} {p.xp}/{p.level*15}  "
              f"{B}GOLD{R} {p.gold}  {B}FLOOR{R} {self.level}")
        print()

        # Messages (last 3)
        for msg in self.messages[-3:]:
            print(f"  {msg}")
        print()
        print(f"  {DIM}hjkl/yubn:move  p:rest  .:wait  q:quit{R}")


# ── Input ───────────────────────────────────────────────────────────
def get_key():
    try:
        import tty, termios
        fd = sys.stdin.fileno()
        old = termios.tcgetattr(fd)
        try:
            tty.setraw(fd)
            ch = sys.stdin.read(1)
            # Handle escape sequences
            if ch == "\x1b":
                ch2 = sys.stdin.read(1)
                if ch2 == "[":
                    ch3 = sys.stdin.read(1)
                    arrow_map = {"A": "k", "B": "j", "C": "l", "D": "h"}
                    return arrow_map.get(ch3, "")
                return ""
            return ch
        finally:
            termios.tcsetattr(fd, termios.TCSADRAIN, old)
    except (ImportError, AttributeError):
        return input("Action: ").strip()[:1] or "."


MOVE_KEYS = {
    "h": (-1, 0), "j": (0, 1), "k": (0, -1), "l": (1, 0),
    "y": (-1, -1), "u": (1, -1), "b": (-1, 1), "n": (1, 1),
}

# ── Main ────────────────────────────────────────────────────────────
def main():
    game = Game()
    game.render()

    while game.player.hp > 0:
        key = get_key()
        if key == "q":
            print("\n  Farewell, adventurer!\n")
            break
        elif key in MOVE_KEYS:
            dx, dy = MOVE_KEYS[key]
            game.move_player(dx, dy)
        elif key == ".":
            game.monster_turn()
        elif key == "p":
            game.use_potion_auto()

        game.render()

    if game.player.hp <= 0:
        print(f"\n  {'='*40}")
        print(f"  GAME OVER — Floor {game.level}, Level {game.player.level}")
        print(f"  Gold: {game.player.gold}  XP: {game.player.xp}")
        print(f"  {'='*40}\n")


if __name__ == "__main__":
    main()
