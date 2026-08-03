# streaks

A tiny, dependency-free habit streak tracker for the command line.
Data is stored as JSON in `~/.streaks.json` (override with `--path`).

## Install

```bash
pip install -e .
```

## Usage

```bash
streaks add read          # create a habit
streaks check read        # check off today
streaks check read --date 2026-08-01   # check off a specific day
streaks uncheck read --date 2026-08-01 # remove a check
streaks status            # show all habits
streaks status read       # show one habit
streaks remove read       # delete a habit
```

`status` reports the current streak, the longest streak, and total days checked.

## Tests

```bash
python -m unittest discover -s tests
```

## Layout

- `streaks/cli.py` — argument parsing and commands
- `streaks/store.py` — JSON persistence
- `streaks/streak.py` — streak calculation logic
