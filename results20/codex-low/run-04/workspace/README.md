# focus-timer

A tiny, **zero-dependency** Pomodoro-style focus timer for your terminal,
written in pure Python (stdlib only).

## Install

```bash
pip install -e .
```

## Usage

```bash
focus                            # 25 min focus + 5 min break
focus --focus 50 --break 10      # custom lengths (minutes, floats allowed)
focus --minutes 1                # run one minute total
```

Press `Ctrl-C` anytime to stop early.

## How it works

- `focus_timer/core.py` — pure, time-independent timer logic (easy to unit test).
- `focus_timer/cli.py` — live terminal UI with colored progress bars.

## Tests

```bash
python -m unittest discover -s tests -v
```
