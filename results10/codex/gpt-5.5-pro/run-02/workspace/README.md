# Pulse

A tiny local decision and note log.

`pulse.py` stores entries as newline-delimited JSON, so the data stays easy to
diff, search, and back up.

## Usage

```bash
python3 pulse.py add "Use SQLite for the prototype" --tag backend --why "simple local state"
python3 pulse.py list
python3 pulse.py show 1
python3 pulse.py export-md
```

By default, entries are written to `pulse.jsonl` in the current directory. Use
`--file path/to/log.jsonl` before the command to choose another file:

```bash
python3 pulse.py --file notes.jsonl add "Ship the narrow version first" --tag scope
```

## Tests

```bash
python3 -m unittest
```
