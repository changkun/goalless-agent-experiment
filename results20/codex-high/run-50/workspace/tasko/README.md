# Tasko

A tiny, dependency-free command-line task manager. Store tasks in a single
JSON file (`~/.tasko.json` by default) with priorities, due dates, tags, and
completion status.

## Quick start

```bash
./tasko.py add "Ship the release" -p high -d friday -t work
./tasko.py add "Reply to emails" -d today -t inbox
./tasko.py add "Groceries" -t personal
./tasko.py list --sort priority -a
./tasko.py done 1
./tasko.py priority 2 high
./tasko.py delete 3
```

## Commands

| Command | Description |
| --- | --- |
| `add TITLE` | Add a task (`-p`, `-d`, `-t` options) |
| `list` / `ls` | List open tasks; `-a` all, `-s open\|done`, `-p`, `-t`, `--sort` |
| `done ID` | Mark a task completed |
| `undo ID` | Reopen a task |
| `delete ID` / `rm ID` | Delete a task |
| `clear [--done]` | Clear all (or only completed) tasks |
| `priority ID low\|normal\|high` | Change a task's priority |

## Options

- `--file PATH` — Use a custom data file (also via `TASKO_FILE`).

## Due dates

`due` accepts `YYYY-MM-DD`, `today`, `tomorrow`, or a weekday name
(e.g. `friday` = the next Friday).

Colors are auto-disabled when output is not a TTY.
