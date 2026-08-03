# terminal-todo

A tiny, dependency-free terminal task manager written in pure Python
(standard library only).

## Features
- Add, list, edit, complete, delete and clear tasks
- Priorities (`low`, `normal`, `high`) and optional due dates
- Overdue highlighting and a simple interactive TUI
- Atomic JSON persistence — safe against interrupted writes

## Usage

Run from a `todo.json` in the current directory, or use `--file`:

```bash
# add
python -m todo_app add "Buy milk" --priority high --due 2026-08-10

# list (open / done)
python -m todo_app list
python -m todo_app list --open
python -m todo_app list --done

# complete / reopen / edit / delete / clear
python -m todo_app done 3
python -m todo_app undo 3
python -m todo_app edit 3 --title "New title" --priority low
python -m todo_app rm 3
python -m todo_app clear

# interactive mode
python -m todo_app interactive
```

There is also a `todo` console script once installed:

```bash
pip install -e .
todo add "hello"
```

## Interactive mode commands

```
a  <title> p=high due=DATE   add a task
d <id> | done <id>           mark done
u <id> | undo <id>           mark open
e <id> title=... priority=.. edit a task
rm <id> | del <id>           delete a task
clear                        remove completed tasks
ls                           refresh
help / q                     help / quit
```

## Tests

```bash
python -m unittest discover -s tests -v
```
