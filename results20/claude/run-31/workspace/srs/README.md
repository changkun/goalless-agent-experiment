# srs — a tiny spaced-repetition flashcard CLI

A zero-dependency flashcard tool implementing the classic SM-2 scheduling
algorithm (the one Anki is based on). Cards are stored in a JSON file via an
atomic write so progress survives interruption.

## Usage

```sh
python3 srs.py add "What is the capital of France?" "Paris"
python3 srs.py add "2 + 2" "4" "math"        # put it in a named deck
python3 srs.py review                        # review due cards (all decks)
python3 srs.py review math                   # review one deck
python3 srs.py stats                         # deck statistics
python3 srs.py newdeck "physics"
```

During review you grade each card 0–5 after seeing the answer:

- **0–2** — failed / forgot (interval resets to 1 day, ease drops)
- **3** — hard (shortened interval, small ease drop)
- **4** — good (standard interval growth)
- **5** — easy (faster growth, ease rises)

## Notes

- Data file is `cards.json` in the working directory; override with the
  `SRS_FILE` environment variable.
- Progress is saved after **every** card, so Ctrl-C mid-review loses nothing.
- `cards.json` is the only artifact you need to back up.

## Tests

```sh
python3 -m unittest test_srs -v
```
