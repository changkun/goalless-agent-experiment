# todo

A tiny, dependency-free task manager that stores your tasks in Markdown, so
they stay portable, human-readable, and diffable in git.

## Requirements

- Python 3.10+

## Quick start

```sh
# point at the file you want to use (default: ~/.todo.md)
export TODO_FILE=$PWD/example.md   # or pass --file each time

./todo.py add "Buy groceries" --priority high --tag errands --due 2026-08-05
./todo.py add "Reply to Kim" --tag work
./todo.py list
./todo.py list --all --tag work
./todo.py done 1
./todo.py rm 2
./todo.py edit 1 "Buy groceries and a cake"
```

## Command reference

| Command | Description |
| --- | --- |
| `add TEXT [--priority P] [--tag T ...] [--due YYYY-MM-DD]` | Add a task |
| `list [--all] [--tag T] [--plain]` | List tasks (open by default) |
| `done INDEX` | Mark task done |
| `rm INDEX` | Remove task |
| `edit INDEX TEXT` | Rewrite task text |

Indices shown by `list` are the ones to use with `done`/`rm`/`edit`.

## Task file format

Each line is one task:

```markdown
- [x] (high) [errands][home] Buy groceries (due 2026-08-05)
```

- `[x]` / `[ ]` — completion state
- `(high|medium|low)` — priority (defaults to medium)
- `[tag]` — zero or more tags
- `(due YYYY-MM-DD)` — optional due date
- Anything after that is the task text

Run `./todo.py --help` for details.
