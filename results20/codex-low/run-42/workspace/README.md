# todos

A tiny, friendly task tracker that persists to JSON — no dependencies, just Python 3.

## Usage

```bash
python3 todos.py add "write a poem" --priority high
python3 todos.py list
python3 todos.py done 2 3
python3 todos.py stats
python3 todos.py clear
```

Tasks are stored in `~/.todos.json` by default. Point `TODOS_FILE` at another path to redirect storage (handy for tests or custom locations).

## Priorities

`high` 🔥, `medium` 📌, `low` 🌱. Completed tasks show `✅`.

## Tests

```bash
python3 -m unittest test_todos -v
```
