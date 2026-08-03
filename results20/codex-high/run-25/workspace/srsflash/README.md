# srsflash

A tiny spaced-repetition flashcards CLI built on the [SM-2 algorithm](https://en.wikipedia.org/wiki/SuperMemo#Description_of_SM-2).

## Features

- Add, list, and remove flashcards
- Interactive review session with self-grading (0-5)
- SM-2 scheduling: intervals grow with repeated success, lapse on failure
- Persistence to a JSON deck file

## Usage

```bash
# Add cards
python3 -m srsflash.cli --deck deck.json add "Capital of France?" "Paris"

# List all cards (due/un-due marked)
python3 -m srsflash.cli --deck deck.json list

# Review due cards (grade yourself 0-5 per card)
python3 -m srsflash.cli --deck deck.json review

# Remove a card by 1-based index
python3 -m srsflash.cli --deck deck.json remove 1
```

## Run tests

```bash
PYTHONPATH=. python3 -m unittest discover -s tests -v
```
