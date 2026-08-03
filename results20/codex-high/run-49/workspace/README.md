# Pomodoro

A tiny, dependency-free Pomodoro focus timer for your terminal.

## Features

- Counts down focus sessions and auto-switches to short/long breaks.
- Long break after every N focus sessions (default: 4).
- Configurable durations via command-line flags.
- Pure, non-blocking core (`pomodoro/core.py`) that's easy to test and reuse.
- `--non-interactive` mode for single-line output (great for scripts/logs).

## Install / run

No third-party dependencies — just Python 3.9+.

```bash
# run from the repository root
python3 -m pomodoro --focus 25 --short-break 5 --long-break 15 --cycle 4
```

Press `Ctrl+C` to stop.

### Options

| Flag            | Default | Meaning                                   |
| --------------- | ------- | ----------------------------------------- |
| `--focus`       | `25`    | Focus session length (minutes)            |
| `--short-break` | `5`     | Short break length (minutes)              |
| `--long-break`  | `15`    | Long break length (minutes)               |
| `--cycle`       | `4`     | Focus sessions before a long break        |
| `--non-interactive` | off | Single-line output without redraws    |

## Usage as a library

```python
from pomodoro import Timer

timer = Timer(focus_minutes=1, short_break_minutes=1, long_break_minutes=1)
completed = timer.tick(60)  # returns the finished Session, or None
print(timer.session_type, timer.remaining)
```

## Tests

```bash
python3 -m unittest discover -s tests -v
```
