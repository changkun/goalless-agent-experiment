# Habits

A tiny, zero-dependency habit tracker CLI with streaks and daily check-ins.

## Install

It's a single Python package; add it to your `PYTHONPATH` or run the launcher directly.

```bash
export PYTHONPATH="$PWD"
./habits.py --help
```

Optionally install as a script:

```bash
pip install .
```

## Usage

```bash
# Add a habit
habits add "Morning run"

# Mark it done today (default) or on a specific day
habits done "Morning run"
habits done "Morning run" --date 2026-08-01

# Undo a check-in
habits undo "Morning run"

# List habits, sorted by activity by default
habits list
habits list --sort name

# Delete a habit and its history
habits remove "Morning run"
```

## Data

Habits are stored as JSON in `~/.habits/habits.json` by default. Override with
`--store /path/to/file.json`. The file is human-readable:

```json
{
  "morning run": {
    "name": "Morning run",
    "created": "2026-08-03",
    "completions": ["2026-08-03"]
  }
}
```

## Commands

| Command  | Description                            |
|----------|----------------------------------------|
| `add`    | Create a new habit                     |
| `done`   | Mark done for a day                    |
| `undo`   | Remove a check-in for a day            |
| `list`   | Show habits with streaks and totals    |
| `remove` | Delete a habit and its history         |

## Development

Run tests:

```bash
python -m unittest discover -s tests
```
