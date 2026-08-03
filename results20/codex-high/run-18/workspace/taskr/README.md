# taskr

A tiny, dependency-free command-line task tracker written in Python (stdlib only).

## Usage

```bash
./taskr.py add buy milk
./taskr.py list
./taskr.py list --status todo
./taskr.py update <id>                  # marks a task done
./taskr.py update <id> --status in_progress
./taskr.py update <id> --description final draft
./taskr.py delete <id>
```

Tasks are stored as JSON in `~/.taskr.json` by default. Use `--file <path>` to
use a different location.

## Statuses

`todo`, `in_progress`, `done`

## Tests

```bash
python3 -m unittest test_taskr.py
```
