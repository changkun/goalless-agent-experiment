# habits

A tiny, dependency-free habit and streak tracker with a JSON-backed store and a
command-line interface. Written for Python 3.10+.

## Features

- Create, check in on, and remove habits.
- Automatic current-streak and total-day counts.
- Persistent storage in a human-readable JSON file.
- No third-party dependencies — stdlib only.

## Install (optional)

```sh
pip install -e .
```

If you install it, you get a `habits` command. Otherwise run via `python -m habits`.

## Usage

```sh
# Create a habit with some backdated check-ins
habits --store ~/.habits.json add "read" -d 2026-08-01 -d 2026-08-02 -d 2026-08-03

# Check in on a habit (defaults to today)
habits check "read"

# Remove a check-in
habits uncheck "read"

# List habits with streaks
habits list

# Delete a habit
habits remove "read"
```

Without installing, prefix with `python -m`:

```sh
python -m habits list
```

## Streak rules

A streak counts consecutive check-in days ending today. Missing today doesn't
break the streak that stretched through yesterday, but a gap of two or more
days resets it to zero. `longest_streak()` reports your best-ever run.

## Tests

```sh
python -m unittest discover -s tests -v
```
