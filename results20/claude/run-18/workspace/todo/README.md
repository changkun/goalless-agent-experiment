# todo

A zero-dependency, single-file command-line task manager written in Python 3.
No pip installs, no config — just run it. Tasks live in `~/.todo.json`.

## Quick start

```bash
./todo.py add "Write the final report" -p high -d 2026-08-05 -t work
./todo.py add "Buy milk" -p low
./todo.py list
```

## Commands

| Command | Description |
| --- | --- |
| `add <title> [-p pri] [-d DATE] [-t tag]...` | Add a task (`pri`: low/medium/high) |
| `list [--done] [-t tag] [-s pri] [-a]` | List tasks. Default shows open; `-a` also shows done |
| `done <id>` | Mark a task completed |
| `undo <id>` | Reopen a task |
| `edit <id> [title] [-p pri] [-d DATE] [-t tag]...` | Update a task |
| `rm <id>` | Delete a task |
| `purge` | Delete all completed tasks |
| `stats` | Show summary counts |

## Features

- Priorities (`high` / `medium` / `low`), due dates, and tags
- Sorting: open first, then by due date, then priority
- `TODAY` / `OVERD` markers in the due-date column
- Atomic saves (write to temp file, then rename) so the store is never corrupted
- Id-based commands; ids are stable across edits

## Details

- Storage file: `~/.todo.json` (override via the `HOME` env var for testing)
- Requires Python 3.9+ (`dict` ordering and `functools` used are all stdlib)
- Error handling: bad ids, bad dates, and missing titles produce clear messages
  and a non-zero exit code
