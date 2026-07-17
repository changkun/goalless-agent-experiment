#!/usr/bin/env python3
"""Drive the TUI inside a pseudo-terminal and verify its screen output.

Spawns `life.py` attached to a pty (so it believes it has a real terminal),
lets it run, sends keystrokes, then quits and asserts on the captured byte
stream: alt-screen enter/exit, HUD contents, generation advance, clean exit.
"""

import fcntl
import os
import pty
import re
import select
import struct
import sys
import termios
import time

LIFE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "life.py")


def drain(fd: int, buf: bytearray, seconds: float) -> None:
    end = time.monotonic() + seconds
    while time.monotonic() < end:
        r, _, _ = select.select([fd], [], [], 0.05)
        if r:
            try:
                chunk = os.read(fd, 65536)
            except OSError:
                return
            if not chunk:
                return
            buf.extend(chunk)


def main() -> int:
    pid, fd = pty.fork()
    if pid == 0:
        # Child: becomes the TUI with the pty as its controlling terminal.
        os.environ["TERM"] = "xterm-256color"
        os.environ["LINES"] = "30"
        os.environ["COLUMNS"] = "100"
        os.execvp(sys.executable, [sys.executable, LIFE, "--speed", "30",
                                   "--seed", "3"])
        os._exit(127)

    # Give the pty a real window size before the child reads it.
    fcntl.ioctl(fd, termios.TIOCSWINSZ,
                struct.pack("HHHH", 30, 100, 0, 0))

    buf = bytearray()
    drain(fd, buf, 1.5)            # let it animate ~45 generations at 30/s
    os.write(fd, b" ")             # pause
    drain(fd, buf, 0.3)
    os.write(fd, b".")             # single step while paused
    drain(fd, buf, 0.3)
    os.write(fd, b"p")             # cycle palette
    drain(fd, buf, 0.3)
    os.write(fd, b"q")             # quit
    drain(fd, buf, 1.0)

    _, status = os.waitpid(pid, 0)
    exit_code = os.waitstatus_to_exitcode(status)
    text = buf.decode("utf-8", errors="replace")

    failures = []

    if "\x1b[?1049h" not in text:
        failures.append("never entered alternate screen")
    if "\x1b[?1049l" not in text:
        failures.append("never restored main screen")

    gens = [int(m) for m in re.findall(r"gen\s+(\d+)", text)]
    if not gens:
        failures.append("HUD generation counter never rendered")
    elif max(gens) < 20:
        failures.append(f"animation barely advanced (max gen {max(gens)})")

    pops = [int(m) for m in re.findall(r"pop\s+(\d+)", text)]
    if not pops or max(pops) == 0:
        failures.append("population never rendered or always zero")

    if "gen/s" not in text:
        failures.append("speed indicator missing from HUD")
    if "embers" not in text:
        failures.append("palette key 'p' did not switch to embers")
    if exit_code != 0:
        failures.append(f"child exited with code {exit_code}")

    # Paused single-step: two consecutive draws differing by exactly one gen.
    step_pairs = [(a, b) for a, b in zip(gens, gens[1:]) if b == a + 1]
    if not step_pairs:
        failures.append("no +1 generation step observed (pause/step broken?)")

    if failures:
        for f in failures:
            print(f"FAIL: {f}")
        return 1
    print(f"TUI smoke test passed "
          f"(gens up to {max(gens)}, pop up to {max(pops)}, "
          f"exit {exit_code})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
