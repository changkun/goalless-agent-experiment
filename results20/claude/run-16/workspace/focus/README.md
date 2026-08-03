# focus — a terminal Pomodoro timer

A distraction-free focus timer that runs entirely in your terminal, built with
only the Python standard library. It keeps a local log of every session so you
can see how you actually spent your time.

## Features

- **Pomodoro with sensible defaults** — 25 min focus / 5 min short break /
  15 min long break (every 4th). All lengths configurable.
- **Live animated progress bar** with elapsed/remaining time.
- **Keyboard controls** — no need to Ctrl-C and lose your session:
  - `space` — pause / resume
  - `s` — skip the current phase
  - `r` — reset the current phase
  - `q` — quit (session is logged)
- **Long-break cadence** — automatically a long break after every 4th focus block.
- **Session logging** — every focus session is appended to `~/.focus/log.csv`
  with timestamps and duration, so you can review how much you focused each day.

## Usage

```bash
python3 focus.py              # default 25/5/15
python3 focus.py --focus 50 --short 10 --long 20
python3 focus.py --cycles 4   # long break every 4th focus block
python3 focus.py --log /path/to/log.csv   # custom log location
```

Type `focus.py --help` for the full list of options.

## Why

I wrote this to replace the tab-chasing / browser-open temptation of social
sites with something that lives quietly in a terminal tab. No dependencies,
no network, no accounts — just a countdown, a file, and you.
