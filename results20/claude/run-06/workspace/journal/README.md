# journal

A tiny, dependency-free command-line journal with habit streak tracking.
Python 3.10+, stdlib only.

## Install & run

```sh
cd journal
python3 -m journal add wrote some code     # append today's entry
python3 -m journal today                   # today's entries + habit streaks
python3 -m journal habit add run           # create a habit
python3 -m journal habit done run          # mark it done for today
python3 -m journal habit list              # streaks
```

Data is stored at `~/.journal.json`. Override with the `JOURNAL_FILE` env var
or `--file`.

## Streak rules

A streak counts consecutive days ending today; if today isn't marked yet it
counts back from yesterday (so an unmarked today doesn't break a streak until
the day is over). A gap at any point resets it to zero for the days after.

## Tests

```sh
cd journal
PYTHONPATH=src python3 -m unittest discover -s tests -v
```
