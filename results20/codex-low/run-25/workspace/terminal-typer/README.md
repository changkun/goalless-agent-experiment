# terminal-typer

A tiny, no-dependency terminal typing game written in Python.

Words fall from the top of your terminal. Type the word whose start matches
your buffer to clear it and earn points. The game gets faster the longer you
survive.

## Run

```bash
python3 main.py
```

Requires Python 3 and a real terminal (`tty`). It uses raw input mode, so it's
best run directly in a terminal, not through a pager.

## Controls

- Type letters to build your buffer
- `Backspace` to delete a character
- `Enter` to clear the current buffer
- `Ctrl-C` to quit

## How scoring works

- `+1` per character typed
- `+10` bonus per word cleared
- `wpm` is tracked as words-per-minute from total typed characters

## Files

- `main.py` — the whole game in one file
