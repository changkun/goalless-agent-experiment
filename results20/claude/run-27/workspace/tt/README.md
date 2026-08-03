# tt — a tiny task tracker

A zero-dependency task tracker in a single Python file. No pip install, no
database, no config — tasks live in one JSON file, and everything fits in a
few commands.

## Install

```bash
./tt --help          # just run it from here
ln -s "$PWD/tt" ~/bin/tt    # or drop it on your PATH
```

## Usage

```
tt add "buy milk"     add a task
tt list               list tasks (aliases: ls)
tt done 1             mark #1 done
tt undo 1             reopen #1
tt delete 1           remove #1 (alias: rm)
tt clear              remove all completed tasks
tt version
```

Output is coloured when stdout is a TTY and plain when piped, so it plays
nicely with `tt list | grep milk`. The store lives at `~/.tt/tasks.json`;
set `TT_STORE` to use another file.

## Design notes

Tasks are stored as JSON, e.g.:

```json
[
  {
    "id": 1,
    "text": "buy milk",
    "done": false,
    "created_at": 1764732600.0,
    "done_at": null
  }
]
```

- `_save` writes to a temp file and `os.replace`s it into place, so a crash
  mid-write can't corrupt the store.
- Commands are plain functions keyed off argparse subparsers and dispatched
  via a `func` attribute, which keeps each command a 5-line unit that's easy
  to test in isolation.
- All user-facing errors are raised as `StoreError` and handled in one place
  in `main`, giving consistent `exit 1` behaviour.

## Tests

```bash
python3 -m pytest test_tt.py            # if you have pytest
python3 test_tt.py                      # or with the stdlib runner
```
