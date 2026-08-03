# drop 🍅

A tiny terminal Pomodoro focus timer in pure Python (stdlib only, no deps).

## Usage

```sh
./pomodoro.py                # 4x 25min focus with short/long breaks
./pomodoro.py -n 2           # just 2 focus sessions
./pomodoro.py -f 50 -s 10    # 50min focus, 10min short break
./pomodoro.py --log          # summary of the last 7 days
./pomodoro.py --today        # summary of today only
./pomodoro.py --days 30 --log
```

While a block runs you can interrupt with `Ctrl+C` and choose to
**resume**, **abandon**, or **skip** it.

## Options

| Flag | Default | Meaning |
|------|---------|---------|
| `-f, --focus` | 25 | focus length in minutes |
| `-n, --count` | 4 | number of focus sessions |
| `-s, --short` | 5 | short break in minutes |
| `-l, --long` | 15 | long break in minutes |
| `--cycles` | 4 | focus sessions before a long break |
| `--log` | — | show history summary |
| `--days` | 7 | days of history to show |
| `--today` | — | show only today |

## Data

Sessions are logged as JSON to
`$XDG_DATA_HOME/drop/sessions.json`
(or `~/.local/share/drop/sessions.json` by default).

## Tests

```sh
python3 -m unittest test_pomodoro -v
```
