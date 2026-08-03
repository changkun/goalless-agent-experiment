# focus

A dependency-free command-line task tracker with a built-in Pomodoro timer.
Uses only the Python standard library — no install-time dependencies.

## Install

```bash
pip install -e .
```

Or run directly from the source tree:

```bash
python -m focus.cli --help
```

## Commands

| Command                   | Description                                     |
| ------------------------- | ----------------------------------------------- |
| `focus add <title>`       | Add a new task (optionally `-t tag,tag`)        |
| `focus list` / `ls`       | List open tasks (add `-a` for completed too)    |
| `focus done <id>`         | Mark a task completed                           |
| `focus reopen <id>`       | Reopen a completed task                         |
| `focus rm <id>`           | Remove a task entirely                          |
| `focus clear`             | Remove all completed tasks                      |
| `focus focus [id]`        | Run a Pomodoro on a task (defaults to oldest)   |
| `focus start [minutes]`   | Run a plain countdown timer                     |
| `focus stats`             | Show summary statistics                          |

## Examples

```bash
focus add "Write blog post" -t writing,work
focus add "Water the plants"
focus ls
focus done 1
focus focus 2          # 25-minute pomodoro on task 2
focus focus -m 5 2     # 5-minute pomodoro
focus stats
```

## Storage

State lives in a JSON file. The location follows the XDG data directory on
Linux/macOS and `%APPDATA%` on Windows. Override it with the `FOCUS_DIR`
environment variable (handy for testing):

```bash
export FOCUS_DIR="$HOME/.mydata/focus"
```

## Development

```bash
python -m unittest discover -s tests -v
```
