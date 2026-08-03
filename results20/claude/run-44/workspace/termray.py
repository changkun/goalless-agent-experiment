#!/usr/bin/env python3
"""
termray — a tiny first-person raycaster that runs in your terminal.

Pure Python, stdlib only. The classic DDA raycasting technique from
Wolfenstein 3D: for each screen column we march a ray through a grid and
find the first wall it hits; its distance tells us how tall and how bright
to draw that column. Sprites are billboards drawn after the walls, hidden
where the wall z-buffer says they should be.

Run it:
    python3 termray.py            interactive (WASD + arrow keys to look)
    python3 termray.py --demo     headless, prints frames as text (no TTY needed)
    python3 termray.py --help     options

WASD / arrows  move and turn        q or Esc  quit
"""

from __future__ import annotations

import argparse
import math
import os
import sys
import time

# ---------------------------------------------------------------------------
# Tiny deterministic PRNG so --demo frames are reproducible run to run.
# ---------------------------------------------------------------------------

class LCG:
    def __init__(self, seed=1):
        self.state = seed & 0xFFFFFFFF
        self.mask = 0xFFFFFFFF

    def next(self, bits=32):
        self.state = (self.state * 1103515245 + 12345) & self.mask
        return self.state >> (32 - bits)

    def rand01(self):
        return self.next(32) / float(2**32)

    def randint(self, lo, hi):
        return lo + self.next(32) % (hi - lo + 1)


# ---------------------------------------------------------------------------
# Ramp of glyphs. Columns farther away are rendered dimmer by stepping up
# toward the spacers; the nearest columns get the full, chunky glyphs.
# ---------------------------------------------------------------------------

DEFAULT_SHADING = " ..:=*#%@"

# The wall map, legend:
#   #  wall
#   .  floor
#   @  demon (a bouncing sprite)
#   +  treasure (a blinking sprite)
MAP_ROWS = [
    "##############",
    "#......#.....#",
    "#.@....#..+..#",
    "#......#.....#",
    "#..@...#.....#",
    "#............#",
    "#.....##.....#",
    "#......@.....#",
    "#....#......+#",
    "#....#....@..#",
    "#....#.......#",
    "############..",
]
H = 12
W = max(len(r) for r in MAP_ROWS)

WALL = "#"
DEMON = "@"
TREASURE = "+"


class Sprite:
    __slots__ = ("x", "y", "char", "vx", "vy", "amp", "period", "bob")

    def __init__(self, x, y, char, vx=0.0, vy=0.0, amp=0.0, period=0.0):
        self.x = x
        self.y = y
        self.char = char
        self.vx = vx
        self.vy = vy
        self.amp = amp
        self.period = period
        self.bob = 0.0  # -1..1, drives the vertical bounce


def build_map():
    grid = [list(r) for r in MAP_ROWS]
    sprites = []
    for y, row in enumerate(MAP_ROWS):
        for x, ch in enumerate(row):
            if ch in (DEMON, TREASURE):
                rng = LCG(x * 31 + y * 17 + 7)
                sprites.append(
                    Sprite(
                        x + 0.5,
                        y + 0.5,
                        ch,
                        vx=rng.rand01() * 0.10 - 0.05,
                        vy=rng.rand01() * 0.10 - 0.05,
                        amp=rng.rand01() * 0.6 + 0.1,
                        period=1.2 + rng.rand01() * 1.6,
                    )
                )
                grid[y][x] = "."
    return grid, sprites


def find_spawn(grid):
    for y in range(H):
        for x in range(W):
            if grid[y][x] == ".":
                return x + 0.5, y + 0.5
    raise RuntimeError("no floor tile to spawn on")


# ---------------------------------------------------------------------------
# Rendering
# ---------------------------------------------------------------------------

def render(width, height, player_x, player_y, dir_x, dir_y, plane_x, plane_y,
           grid, sprites, time_s, shading):
    """Render one frame; returns (chars, zbuf) where zbuf is the wall distance
    per column (used for sprite occlusion)."""
    chars = []
    zbuf = [0.0] * width
    ramp = shading
    n_ramp = len(ramp)

    for x in range(width):
        # Ray direction through this column, in camera space.
        cam_x = 2.0 * x / width - 1.0
        ray_x = dir_x + plane_x * cam_x
        ray_y = dir_y + plane_y * cam_x

        map_x = int(player_x)
        map_y = int(player_y)

        # Unit stepping direction + first distance to a cell boundary.
        if ray_x == 0.0:
            step_x, side_dist_x = 0, math.inf
        elif ray_x > 0.0:
            step_x = 1
            side_dist_x = (map_x + 1.0 - player_x) / ray_x
        else:
            step_x = -1
            side_dist_x = (player_x - map_x) / -ray_x
        if ray_y == 0.0:
            step_y, side_dist_y = 0, math.inf
        elif ray_y > 0.0:
            step_y = 1
            side_dist_y = (map_y + 1.0 - player_y) / ray_y
        else:
            step_y = -1
            side_dist_y = (player_y - map_y) / -ray_y

        # DDA march. deltaDist is how far along the ray to travel one full
        # cell in that axis; sideDist is why we incrementally add it.
        delta_dist_x = abs(1.0 / ray_x) if ray_x != 0 else math.inf
        delta_dist_y = abs(1.0 / ray_y) if ray_y != 0 else math.inf
        side = 0
        while True:
            if side_dist_x < side_dist_y:
                side_dist_x += delta_dist_x
                map_x += step_x
                side = 0
            else:
                side_dist_y += delta_dist_y
                map_y += step_y
                side = 1
            if grid[map_y][map_x] == WALL:
                break

        # Perpendicular distance to the wall (fish-eye corrected). The loop
        # advanced side_dist one step too far (into the wall cell), so back
        # off a single delta.
        perp = side_dist_x - delta_dist_x if side == 0 else side_dist_y - delta_dist_y
        perp = max(perp, 1e-6)
        zbuf[x] = perp

        line_h = height / perp
        draw_start = int(-line_h / 2 + height / 2)
        draw_end = int(line_h / 2 + height / 2)

        # ramp[0] is the background space — never use it for walls, so clamp
        # the whole ramp to indices [1, n_ramp-1].
        shade_idx = max(1, min(int(perp) + (0 if side == 0 else 1), n_ramp - 1))
        wall_ch = ramp[shade_idx]

        for y in range(height):
            if y < draw_start or y >= draw_end:
                chars.append(" ")
            elif side == 1:
                # Skew the char every other row so north/south walls read
                # as a slightly different texture from east/west ones.
                chars.append(wall_ch if (y & 1) == 0 else ramp[max(1, shade_idx - 1)])
            else:
                chars.append(wall_ch)
    return chars, zbuf


# ---------------------------------------------------------------------------
# Sprite pass: project each sprite into camera space, sort far-to-near,
# then stamp it into the frame where the z-buffer lets it.
# ---------------------------------------------------------------------------

def draw_sprites(width, height, player_x, player_y, dir_x, dir_y, plane_x,
                 plane_y, sprites, grid, frame, zbuf, time_s, rng):
    transformed = []
    for s in sprites:
        # world -> camera space
        rel_x = s.x - player_x
        rel_y = s.y - player_y
        inv_det = 1.0 / (plane_x * dir_y - dir_x * plane_y)
        t_x = inv_det * (dir_y * rel_x - dir_x * rel_y)
        t_y = inv_det * (-plane_y * rel_x + plane_x * rel_y)
        transformed.append((t_x, t_y, s))
    transformed.sort(key=lambda t: t[1], reverse=True)  # far first

    fw, fh = len(grid[0]), len(grid)
    for t_x, t_y, s in transformed:
        if t_y <= 0.05:
            continue  # behind the camera
        sprite_x = int((width / 2) * (1 + t_x / t_y))
        sprite_h = abs(int(height / t_y))
        sprite_w = abs(int(height / t_y))
        v_move = int(s.bob * sprite_h * 0.15)

        y0 = max(0, int(height / 2 - sprite_h / 2 + v_move))
        y1 = min(height, int(height / 2 + sprite_h / 2 + v_move))
        x0 = max(0, int(sprite_x - sprite_w / 2))
        x1 = min(width, int(sprite_x + sprite_w / 2))

        ch = s.char
        for sy in range(y0, y1):
            for sx in range(x0, x1):
                if 0 <= sx < width and t_y < zbuf[sx]:
                    frame[sy * width + sx] = ch


def frame_to_str(frame, width, height):
    lines = []
    for y in range(height):
        lines.append("".join(frame[y * width:(y + 1) * width]))
    return "\n".join(lines)


def move_player(x, y, dir_x, dir_y, plane_x, plane_y, grid, forward, strafe, turn):
    speed = 3.0
    turn_speed = 2.2
    rot = turn * turn_speed * (1 / 30.0)

    cos_r, sin_r = math.cos(rot), math.sin(rot)
    dir_x, dir_y = dir_x * cos_r - dir_y * sin_r, dir_x * sin_r + dir_y * cos_r
    plane_x, plane_y = (
        plane_x * cos_r - plane_y * sin_r,
        plane_x * sin_r + plane_y * cos_r,
    )

    nx = x + (dir_x * forward + plane_x * strafe) * speed * (1 / 30.0)
    ny = y + (dir_y * forward + plane_y * strafe) * speed * (1 / 30.0)

    if grid[int(ny)][int(x)] != WALL:
        y = ny
    if grid[int(y)][int(nx)] != WALL:
        x = nx
    return x, y, dir_x, dir_y, plane_x, plane_y


# ---------------------------------------------------------------------------
# Interactive mode
# ---------------------------------------------------------------------------

def interactive():
    import curses

    grid, sprites = build_map()
    x, y = find_spawn(grid)
    dir_x, dir_y = -1.0, 0.0
    plane_x, plane_y = 0.0, 0.66

    stdscr = curses.initscr()
    curses.noecho()
    curses.cbreak()
    stdscr.keypad(True)
    try:
        curses.curs_set(0)
    except Exception:
        pass

    width = max(40, min(120, os.get_terminal_size().columns))
    height = max(20, min(40, os.get_terminal_size().lines))
    shading = DEFAULT_SHADING

    if curses.has_colors():
        curses.start_color()
        curses.use_default_colors()
        curses.init_pair(1, curses.COLOR_RED, -1)
        curses.init_pair(2, curses.COLOR_YELLOW, -1)
        curses.init_pair(3, curses.COLOR_WHITE, -1)
    else:
        stdscr.addstr("(no color) ")

    try:
        while True:
            stdscr.clear()
            stdscr.addstr(0, 0, "termray  WASD move  Arrows look  q quit")
            stdscr.addstr(1, 0, f"pos=({x:.1f},{y:.1f})  dir=({dir_x:.2f},{dir_y:.2f})")

            chars, zbuf = render(width, height, x, y, dir_x, dir_y, plane_x, plane_y,
                                 grid, sprites, 0.0, shading)
            draw_sprites(width, height, x, y, dir_x, dir_y, plane_x, plane_y,
                         sprites, grid, chars, zbuf, 0.0, LCG(1))

            if curses.has_colors():
                for row in range(height):
                    for col in range(width):
                        ch = chars[row * width + col]
                        pair = {DEMON: 1, TREASURE: 2}.get(ch, 3)
                        if ch != " ":
                            try:
                                stdscr.addch(3 + row, col, ch, curses.color_pair(pair))
                            except curses.error:
                                pass
            else:
                for row in range(height):
                    try:
                        stdscr.addstr(3 + row, 0, "".join(chars[row * width:(row + 1) * width]))
                    except curses.error:
                        pass

            # Minimap
            mm_x = width - W - 2
            mm_y = 3
            for my, row in enumerate(grid):
                for mx, cell in enumerate(row):
                    if cell == WALL:
                        ch = "#"
                    elif cell == DEMON:
                        ch = "@"
                    elif cell == TREASURE:
                        ch = "+"
                    else:
                        ch = " "
                    try:
                        stdscr.addch(mm_y + my, mm_x + mx, ch)
                    except curses.error:
                        pass
            try:
                stdscr.addch(mm_y + int(y), mm_x + int(x), "P")
            except curses.error:
                pass

            stdscr.refresh()

            # Move sprites along with their velocity (they bounce off walls).
            for s in sprites:
                s.bob = math.sin(time.monotonic() * s.period * 2.0)
                nx, ny = s.x + s.vx, s.y + s.vy
                if grid[int(ny)][int(nx)] == WALL:
                    s.vx, s.vy = -s.vx, -s.vy
                else:
                    s.x, s.y = nx, ny

            stdscr.timeout(33)
            key = stdscr.getch()
            forward = strafe = turn = 0
            if key == ord("q") or key == 27 or key == ord("Q"):
                break
            elif key in (ord("w"), ord("W"), curses.KEY_UP):
                forward = 1
            elif key in (ord("s"), ord("S"), curses.KEY_DOWN):
                forward = -1
            elif key in (ord("a"), ord("A")):
                strafe = -1
            elif key in (ord("d"), ord("D")):
                strafe = 1
            elif key == curses.KEY_LEFT:
                turn = 1
            elif key == curses.KEY_RIGHT:
                turn = -1

            x, y, dir_x, dir_y, plane_x, plane_y = move_player(
                x, y, dir_x, dir_y, plane_x, plane_y, grid, forward, strafe, turn
            )
    finally:
        curses.nocbreak()
        stdscr.keypad(False)
        curses.echo()
        curses.endwin()


# ---------------------------------------------------------------------------
# Headless demo: render a few frames to plain text so you can see it without
# a terminal. Each frame prints a header then the picture.
# ---------------------------------------------------------------------------

def demo(width=72, height=26, frames=3, seed=7):
    rng = LCG(seed)
    grid, sprites = build_map()
    # A vantage point that frames a nice depth gradient with a sprite in view.
    x, y = 2.5, 2.5

    for i in range(frames):
        # Sweep the camera through a corridor so the parallax shows.
        ang = (i - frames / 2.0) * 0.30 + 0.35
        cx, cy = math.cos(ang), math.sin(ang)
        dx, dy = cx, cy
        pl_x = -cy * 0.66
        pl_y = cx * 0.66

        chars, zbuf = render(width, height, x, y, dx, dy, pl_x, pl_y,
                             grid, sprites, 0.0, DEFAULT_SHADING)
        for s in sprites:
            s.bob = math.sin(i * s.period * 0.9)
        draw_sprites(width, height, x, y, dx, dy, pl_x, pl_y,
                     sprites, grid, chars, zbuf, 0.0, rng)

        sys.stdout.write(f"--- frame {i + 1}  (camera turned {math.degrees(ang):+5.1f}) ---\n")
        sys.stdout.write(frame_to_str(chars, width, height))
        sys.stdout.write("\n\n")


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--demo", action="store_true", help="headless demo, prints frames")
    ap.add_argument("--width", type=int, default=72, help="demo frame width")
    ap.add_argument("--height", type=int, default=26, help="demo frame height")
    ap.add_argument("--frames", type=int, default=3, help="demo frame count")
    ap.add_argument("--seed", type=int, default=7, help="PRNG seed")
    args = ap.parse_args()

    if args.demo:
        demo(width=args.width, height=args.height, frames=args.frames, seed=args.seed)
    else:
        try:
            interactive()
        except Exception as e:  # noqa: BLE001
            sys.stderr.write(f"error: {e}\n")
            sys.exit(1)


if __name__ == "__main__":
    main()
