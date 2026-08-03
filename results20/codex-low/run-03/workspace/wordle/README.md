# Terminal Wordle

A self-contained Wordle game for the terminal, written in pure Python
(standard library only — no dependencies).

## Play

```bash
python3 -m wordle          # random word
python3 -m wordle --answer ROBOT   # specific word
```

Type a 5-letter guess and press Enter. Tiles show:

- 🟩 **green** – letter is correct and in the right spot
- 🟨 **yellow** – letter is in the word but in the wrong spot
- ⬛ **grey** – letter is not in the word

You get 6 guesses. Type `q`, `quit`, or `exit` to give up.

## Test

```bash
python3 -m unittest discover -s tests -v
```

## Layout

- `wordle/game.py` – game logic and guess feedback
- `wordle/cli.py` – terminal UI
- `wordle/words.py` – curated list of 787 answer words
- `tests/test_game.py` – unit tests
