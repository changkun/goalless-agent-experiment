# Wordle CLI

A small, colorful, dependency-free terminal Wordle clone written in Python.

## Install & run

```bash
python3 -m wordle          # run from the repo root
pip install -e . && wordle # install as a command-line tool
```

## How to play

Guess the hidden 5-letter word in up to 6 tries. After each guess, letters
are colored to show how close you are:

- Green — the letter is correct and in the right spot.
- Yellow — the letter is in the word, but in the wrong spot.
- White — the letter is not in the word at all.

Repeated letters follow standard Wordle rules: a repeated letter is only ever
credited for as many times as it appears in the answer.

## Options

```text
usage: wordle [-h] [-n GUESSES] [--no-color] [--answer ANSWER]

-n, --guesses GUESSES  number of allowed guesses (default: 6)
--no-color             disable ANSI colors (shows G / Y / . instead)
--answer ANSWER        force a specific answer (lowercase letters)
```

## Development

```bash
python3 -m unittest discover -s tests   # run the test suite
```

The game logic lives in `wordle/logic.py` (pure, easily testable) and the
terminal UI in `wordle/__main__.py`. The word list in `wordle/words.py`
contains 619 unique 5-letter words.
