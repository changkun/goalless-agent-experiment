# Wordle CLI

A self-contained Wordle-style word game for your terminal, built with only the
Python standard library.

![game](docs/demo.png)

## Features

- Color-coded feedback (green = correct spot, yellow = wrong spot, gray = absent)
- Random 5-letter secret each round
- Persistent stats (games played, wins, streaks, guess distribution)
- No third-party dependencies, works with Python 3.8+

## Run

Without installing:

```bash
./bin/wordle
```

Or install it as a command:

```bash
pip install -e .
wordle
```

### Options

```bash
wordle --word crane        # play with a chosen secret (great for demos)
wordle --no-color          # plain text feedback
wordle --max-attempts 8    # change the number of attempts
```

Set `WORDLE_DATA_DIR` to keep stats somewhere other than `~/.wordle_cli`.

## Test

```bash
python -m unittest discover -s tests
```
