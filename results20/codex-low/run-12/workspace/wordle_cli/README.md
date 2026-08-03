# wordle_cli

A self-contained **Wordle** clone you can play entirely in your terminal.

## Features

- Six-guess classic rules with green / yellow / grey feedback
- Seeded 5-letter word list (no network or external dependencies)
- ANSI colors on terminals, plain output otherwise
- Daily word mode (based on the date) or a random word
- Simple unit tests for the game logic

## Install & run

```bash
pip install -e .
wordle            # random word, interactive
wordle --daily    # word derived from today's date
wordle --word crane   # play a specific hidden word
```

## Play

Type any 5-letter word and press Enter. The letters are colored:

- 🟩 green — correct letter, correct position
- 🟨 yellow — correct letter, wrong position
- ⬜ grey — letter not in the word

## Development

```bash
python -m pytest
python -m wordle_cli
```
