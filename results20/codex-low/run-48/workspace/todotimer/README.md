# todo

A tiny, zero-dependency terminal task tracker with a pomodoro focus timer.

## Features
- Add, list, complete, and remove tasks
- Priorities: `low`, `med`, `high`
- Per-task pomodoro counter from the built-in focus timer
- Persists to `~/.todotimer/tasks.json` (JSON, plain text)

## Usage
```sh
python3 todo.py add "write report" --priority high
python3 todo.py list            # all tasks
python3 todo.py list --incomplete
python3 todo.py done 1          # mark task #1 done
python3 todo.py rm 2            # remove task #2
python3 todo.py focus 1         # 25-min pomodoro for task #1
python3 todo.py focus 1 --minutes 10
```

## Tests
```sh
python3 -m unittest discover -s . -p "test_*.py" -v
```

No third-party dependencies — just Python 3.9+.
