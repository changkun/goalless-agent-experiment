import os, sys, time, math, random, shutil

WIDTH, HEIGHT = shutil.get_terminal_size()
W, H = WIDTH, HEIGHT - 1
CX, CY = W / 2, H / 2

NUM_STARS = 220
SPEED = 0.9
MAX_DEPTH = 28.0

chars = " .',:;iloxX#%@"

class Star:
    def __init__(self):
        self.reset(initial=True)
    def reset(self, initial=False):
        self.x = random.uniform(-1, 1) * W
        self.y = random.uniform(-1, 1) * H
        self.z = random.uniform(1, MAX_DEPTH) if initial else MAX_DEPTH

stars = [Star() for _ in range(NUM_STARS)]

def render():
    buf = [[' '] * W for _ in range(H)]
    for s in stars:
        s.z -= SPEED
        if s.z <= 0:
            s.reset()
            continue
        sx = int(s.x / s.z * 5 + CX)
        sy = int(s.y / s.z * 2.4 + CY)
        if 0 <= sx < W and 0 <= sy < H:
            shade = int((1 - s.z / MAX_DEPTH) * (len(chars) - 1))
            shade = max(0, min(len(chars) - 1, shade))
            buf[sy][sx] = chars[shade]
    return '\n'.join(''.join(row) for row in buf)

def main():
    sys.stdout.write('\033[?25l\033[2J')  # hide cursor, clear
    sys.stdout.flush()
    try:
        while True:
            frame = render()
            sys.stdout.write('\033[H' + frame)
            sys.stdout.flush()
            time.sleep(0.033)
    except KeyboardInterrupt:
        pass
    finally:
        sys.stdout.write('\033[?25h\033[0m\n')
        sys.stdout.flush()

if __name__ == '__main__':
    main()
