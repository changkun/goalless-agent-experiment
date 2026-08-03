# Habit Tracker

A small, dependency-free command-line habit tracker written in Python. It stores
everything in a single JSON file, tracks daily streaks, and has zero external
dependencies beyond the standard library.

## Install

```bash
pip install -e .
```

Then the `habit` command is available. (You can also run it without installing
via `python -m habit_tracker`.)

## Usage

```bash
# Create a habit
habit add "Read 20 pages"

# Mark it complete for today
habit done "Read 20 pages"

# Mark it complete for a specific day (useful for backfilling)
habit done "Read 20 pages" --date 2026-08-01

# Change your mind
habit undo "Read 20 pages"

# List habits with current streak
habit list

# Detailed stats
habit list --verbose

# Remove a habit
habit rm "Read 20 pages"
```

## Data storage

By default, data lives in `~/.habit_tracker.json`. Point to a custom file with
the `--data` flag on any command:

```bash
habit --data ~/my-habits.json list
```

The file is human-readable JSON, so it's easy to back up or migrate. Writes are
atomic (a temp file is written and renamed into place), so a crash mid-save
won't corrupt your data.

## Features

- Current streak: consecutive completed days ending today
- Longest streak: best run ever recorded
- Total completions per habit
- Backfill and undo for any date
- Malformed data is gracefully ignored on load

## Tests

Run the stdlib-based test suite with no installs required:

```bash
python -m unittest discover -s tests
```
