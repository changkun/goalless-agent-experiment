# Pomo

A small, dependency-free **Pomodoro timer** for the terminal, written in pure
Python. It runs a work/break cycle with a live progress bar, records completed
sessions, and reports your focus time.

## Install

Run it directly from the repo:

```bash
python3 -m pomo.cli --help
```

Or install as a package:

```bash
pip install -e .
pomo --help
```

> No third-party dependencies. Requires Python 3.9+.

## Usage

```bash
# Start the timer (25 min work / 5 min short / 15 min long)
pomo -t "Write blog post"

# Customize phase lengths (minutes)
pomo -w 50 -s 10 -l 30 -n 4

# View focus-time report
pomo report

# Reset recorded stats (with confirmation)
pomo reset --yes
```

Commands:

- `run` (default): start the interactive timer. `Ctrl-C` stops it, saving any
  completed sessions.
- `report`: show a summary of total pomodoros and focus time by day.
- `reset`: clear saved stats (requires `--yes`).

Sessions are stored in `~/.pomo-stats.json` by default; override with
`--stats-path`.

## Design

- `pomo/core.py`: the deterministic, clock-injectable timer engine
  (`PomodoroTimer`), which records each completed session.
- `pomo/stats.py`: JSON persistence and human-readable reporting.
- `pomo/cli.py`: the command-line interface and live terminal display.
- `tests/`: unit tests for the timing engine and stats round-tripping.

The engine never sleeps or sleeps-by-polling on its own; the CLI drives it
with a real monotonic clock while keeping the core deterministic for testing.

## Tests

The test suite uses only the standard library (no pytest required):

```bash
python3 -m unittest discover -s tests -v
```
