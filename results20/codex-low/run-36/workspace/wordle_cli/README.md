# wordle_cli

A tiny Wordle clone for the terminal, written in pure Python (standard library only).

## Play

```bash
python3 cli.py
```

Guesses must be 5 letters and come from the built-in word list.

## Options

- `--answer WORD` — use a fixed word (for testing/practice).
- `--guesses N` — change the number of allowed tries (default 6).

## Feedback

Each guess prints colored dots:

- Green (`G`) — letter is correct and in the right spot.
- Yellow (`Y`) — letter is in the word but wrong spot.
- Gray (`B`) — letter is not in the word.

## Test

```bash
python3 -m unittest test_game -v
```
