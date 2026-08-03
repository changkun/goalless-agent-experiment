# todo

A small, zero-dependency CLI task manager in a single Python file. No third-party
packages, one JSON file for storage, and a clean terminal view with priorities,
projects, and due dates.

```
$ todo add "ship the release" -p high
✔ Added #1: ship the release
   1 open task(s) · 1 total
$ todo add "water plants" --project home --due tomorrow
$ todo add "file taxes" --project finance --due 2026-09-01 -p high
$ todo
To do (3 tasks):
  [ ] ship the release    high
  [ ] water plants        home · due 2026-08-04
  [ ] file taxes          finance · due 2026-09-01
$ todo done 1
✔ Completed #1 · ship the release
```

## Requirements

- Python 3.9+ (uses `pathlib`, `dataclass`-free slots, f-strings)
- No external dependencies

## Install

There's nothing to install — it's a single script. Copy it anywhere and make it
executable, or alias it:

```sh
# Optional: add to PATH
install -m 755 todo.py ~/.local/bin/todo

# or just alias it
alias todo="python3 /path/to/todo.py"
```

## Usage

```
todo [COMMAND] [OPTIONS]
```

### Commands

| Command | Description |
| --- | --- |
| `todo` (no command) | List open tasks |
| `todo add <text>` | Add a task |
| `todo list` | List tasks (same as no command) |
| `todo done <id>` | Mark a task complete |
| `todo remove <id>` | Remove a task (asks for confirmation) |
| `todo clear` | Clear tasks (see options) |

### Options for `add`

| Option | Description |
| --- | --- |
| `-p, --priority <low\|medium\|high>` | Priority (default: `medium`) |
| `--project <name>` | Project tag, e.g. `work`, `home` |
| `-d, --due <date>` | Due date: `YYYY-MM-DD`, `today`, or `tomorrow` |

### Options for `list`

| Option | Description |
| --- | --- |
| `-a, --all` | Include completed tasks |
| `--project <name>` | Only show tasks with this project |
| `-p, --priority <low\|medium\|high>` | Only show tasks at this priority |

### Options for `clear`

| Option | Description |
| --- | --- |
| `-y, --yes` | Skip the confirmation prompt |
| `-d, --done` | Only clear completed tasks |
| `-a, --all` | Clear everything |

Global options:

| Option | Description |
| --- | --- |
| `-f, --file <path>` | Path to the tasks file (see Storage) |
| `--version` | Print version |

## Storage

Tasks live in `~/.todo/tasks.json` by default. Override per-invocation with
`-f/--file`, or for every invocation with the `TODO_FILE` environment variable:

```sh
export TODO_FILE="$HOME/Dropbox/todo.json"   # sync across machines
export TODO_FILE=/tmp/scratch.html           # any filename works
```

The file is written **atomically** (write to a temp file, then rename), so a
crash can never leave a half-written task list.

## Examples

```sh
# Quick captures
todo add "buy milk"
todo add "wire up CI" --project dev -p high
todo add "book dentist" --due tomorrow

# Reviewing
todo                       # open tasks, urgent/overdue first
todo --all                 # include completed ones
todo list --project dev    # just the dev project
todo list -p high          # just high priority

# Updating
todo done 3                # mark #3 complete
todo remove 4              # remove (confirm)
todo remove 4 -y           # remove without asking

# Maintenance
todo clear --done -y       # sweep completed without prompting
```

## How sorting works

Open tasks are ordered by: **overdue first**, then **priority** (high → medium →
low), then **due date**, then id. Completed tasks only appear with `--all` and
sort separately.

## Output

Colors are enabled automatically when stdout is a terminal and stay off when
piped. Set `NO_COLOR=1` to force plain output. Overdue tasks are shown in red,
completed ones are dimmed with a ✔.

## Development

Run the tests:

```sh
python3 -m unittest -v
```

The tests use a throwaway temp file for storage, so they never touch your real
task list.
