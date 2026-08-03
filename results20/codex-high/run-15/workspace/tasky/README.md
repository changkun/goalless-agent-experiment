# tasky

A tiny, zero-dependency command-line task tracker written in Python.

## Install

```bash
pip install -e .
```

Or run it directly from the repo:

```bash
python -m tasky --help
```

## Usage

```bash
# add a task
tasky --file tasks.json add "buy milk"

# list tasks (completed ones sink to the bottom)
tasky --file tasks.json list

# mark done / undo / delete
tasky --file tasks.json done <id>
tasky --file tasks.json undo <id>
tasky --file tasks.json rm <id>

# remove everything
tasky --file tasks.json clear
```

By default tasks are stored in `tasks.json` in the current directory. Point
`--file` somewhere else to keep a separate store. Data is saved on every write.

## Tests

```bash
python -m unittest discover -s tests
```
