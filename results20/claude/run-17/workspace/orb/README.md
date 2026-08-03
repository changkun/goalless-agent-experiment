# orb

A tiny, dependency-free terminal dashboard for your machine. No install, no
third-party packages — just Python 3.8+.

It shows, on a single screen:

- CPU usage and a live **sparkline** of recent load
- Memory used / total, with a proportional **bar**
- Disk usage for the root filesystem
- Uptime, load average, and hostname
- A small rolling **battery-style progress meter** for each metric

## Run it

```bash
python3 orb.py
# or, to refresh every 2 seconds and exit after 60:
python3 orb.py --interval 2 --once
```

- `--interval N`   seconds between refreshes (default 1)
- `--once`         print a single snapshot and exit
- `--demo`         simulate changing metrics (no system data, for screenshots)

## What it does

`orb` reads live numbers straight from `/proc` (Linux) or falls back to
`psutil` if you have it, and renders them with Unicode block characters that
shrink gracefully to the terminal width. It clears the screen between frames,
so it feels like a live dashboard rather than a log.

## Files

- `orb.py` — the whole tool (single file)
- `test_orb.py` — a small test that runs the pure rendering functions
