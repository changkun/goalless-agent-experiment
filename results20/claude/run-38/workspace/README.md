# sysdash — a dependency-free Linux system dashboard

A live terminal system monitor with **zero third-party dependencies**. It reads
Linux `/proc` and `/sys` directly, so it runs on stock CPython with only the
standard library.

```
                        myhost   3h 41m 11s   6 cores
  CPU   ██████████████████████░░░░░░░░░░░░░░░░░░░░░░░░░░░  32.3%
  load    1.38   1.72   2.04
  MEM    ████████████████████░░░░░░░░░░░░░░░░░░░░░░░░░░░░  2.7G/8.3G
  swap   ░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░  0/0
  net    ↓     0/s   ↑     0/s
  /workspace █████████████████████░░░░░░░░░░░░░░░░░░░░░░░  833.5G/994.7G

  CPU %  [0–100]                     MEM %  [0–100]
  (scrolling sparkline history)
```

## Features
- **CPU** util bar + real 1/5/15-minute load average
- **Memory & swap** bars (used/total)
- **Network** cumulative RX/TX rate computed from `/proc/net/dev`
- **Disk** usage per mount, with bind-mounts of the same device deduped
- **Scrolling line chart** of CPU & memory over the last 120 samples
- Press **`q`** to quit; normal terminal state is restored on exit

## Run
```bash
python3 sysdash.py                # live, auto-sized to your terminal
python3 sysdash.py --interval 5   # refresh every 5s
python3 sysdash.py --once         # print a single frame and exit (great for scripting)
python3 sysdash.py --width 100    # fixed width
```

HTML-escape notes: rendered purely with Unicode block chars (`█░`) and
ANSI cursor-motion, no tput/termios black magic.

## Why it exists
`psutil` isn't always available, and a metrics dashboard is a fun self-contained
weekend project. Everything maps 1:1 to kernel interfaces:

| metric            | source                                   |
|-------------------|------------------------------------------|
| CPU %             | `/proc/stat` deltas                       |
| load average      | `/proc/loadavg`                           |
| memory / swap     | `/proc/meminfo`                           |
| network rate      | `/proc/net/dev` deltas                    |
| disk usage        | `statvfs()` on mounts from `/proc/mounts` |
