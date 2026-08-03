# focus

A tiny, zero-dependency **task + pomodoro focus tracker** for the terminal.

Everything lives in one Python file. Tasks and focus sessions persist to
`~/.focus/data.json` as JSON — no database, no network, nothing to install
(just Python 3.8+).

## Install

```bash
# either use the Python module directly:
alias focus="/workspace/focus/focus.py"

# or put the launcher on your PATH:
ln -s /workspace/focus/focus ~/.local/bin/focus
```

## Usage

```
focus add "write report" --tags work     add a task
focus list                                list open tasks
focus list --all --tag work               include done / filter by tag
focus done <id>                           mark complete
focus redo <id>                           reopen
focus rm <id>                             delete
focus focus [--min 25] [--tags work]      run a pomodoro (Ctrl+C to stop early)
focus stats [--days 7]                    focus-time summary with bars
focus dashboard [--port 8321]             serve a local HTML dashboard
focus sync [--days 7]                     prune finished tasks older than 7 days
```

### Pomodoro

`focus focus` runs a 25-minute countdown with a progress bar. Interrupt it
early with **Ctrl+C** — the elapsed time is still saved, so a 17-minute sprint
counts as 17 minutes, not zero.

### Dashboard

`focus dashboard` starts a local web server and prints a URL
(`http://127.0.0.1:8321/dashboard.html`). It shows today's focus minutes,
session counts, a 7-day activity chart, and your open tasks. Light/dark aware,
works in any browser.

## Data & privacy

- Data file: `~/.focus/data.json`
- Override location: `export FOCUS_DATA_DIR=/some/other/dir`
- All local. Nothing leaves your machine.
