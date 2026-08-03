# Mnemo

A minimal spaced-repetition flashcard CLI, written in pure Python (standard
library only — no dependencies). It uses the classic
[SM-2 algorithm](https://en.wikipedia.org/wiki/SuperMemo#Description_of_SM-2_algorithm)
to schedule card reviews at growing intervals, so you review things right
before you're about to forget them.

```
$ mnemo add "2+2" "4"
Added card #1: 2+2

$ mnemo review
2 card(s) due. Enter rating after flipping each card.
Ratings: 0=again  1=hard  2=good  3=easy   (q=quit)

[1] 2+2
    (press Enter to reveal answer)
    4
    rating [0/1/2/3] > 2
    -> next review in 1 day(s)
```

## Install / run

No build step needed. From this directory you can run the module directly:

```
python3 -m mnemo.cli --help
```

Or install it as a command:

```
pip install -e .
mnemo --help
```

## Commands

| Command           | Description                                     |
|-------------------|-------------------------------------------------|
| `add FRONT BACK`  | Add a card.                                     |
| `list`            | List all cards with their scheduling state.     |
| `due`             | Show cards currently due for review.            |
| `review`          | Interactive review session (`-q` for scripting).|
| `stats`           | Deck totals: cards, due, lapses, avg ease.      |

Pass `--db PATH` to any command to use a specific database file. The default
is `~/.mnemo/deck.db`.

## How scheduling works

Each card tracks an **ease** multiplier (default 2.5), a review **interval**
in days, a **reps** count, and a **lapses** count. After each review you rate
recall quality:

- **0 = again**: you forgot — the card *lapses*: ease −0.2, interval resets
  to 1 day.
- **3 = hard / 4 = good / 5 = easy**: successful — interval grows
  (1 → 6 → ~ease× previous), with easy growing faster and hard-slightly
  shaving ease.

The next due date is `today + interval`. Cards are surfaced by `review`/`due`
whenever their due day has arrived.

## Tests

```
python3 -m unittest discover -s tests -v
```

## Structure

```
mnemo/
  sm2.py    # the scheduling algorithm (pure function)
  db.py     # sqlite storage + day/math helpers
  cli.py    # argparse frontend
tests/      # unit tests for sm2 and db
```
