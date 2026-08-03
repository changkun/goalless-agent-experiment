# pomo — a friendly Pomodoro focus timer for the terminal

A dependency-free (Python stdlib only) Pomodoro timer with a live countdown
TUI, persistent config, and a session log.

## Quick start

```sh
python3 pomo.py run          # start a full focus cycle
python3 pomo.py show         # show current configuration
python3 pomo.py stats        # show focus statistics
python3 pomo.py set --work 30 --rounds 4   # change & persist settings
```

## Controls (while a timer is running)

| Key | Action        |
|-----|---------------|
| `p` | pause         |
| `r` | resume        |
| `s` | skip phase    |
| `q` | quit          |

## How it works

A cycle alternates **Focus** sessions with breaks. After the configured number
of focus rounds it takes a **long break**:

```text
Focus → Short break → Focus → Short break → … → Focus → Long break
```

Default timings: 25 min focus, 5 min short break, 15 min long break, 4 rounds
per long-break cycle.

## Configuration & data

- Config: `~/.pomo/config.json` (override the location with `POMO_CONFIG`).
- Session log: `~/.pomo/log.jsonl` — every focus session is appended, and
  `pomo stats` aggregates it.
- Values are validated (durations 1–180 min, rounds 1–12).

## Notifications

Phase changes ring the terminal bell and, where a notifier exists (`notify-send`
on Linux, `osascript` on macOS), post a desktop notification. All gracefully
no-op when unavailable.

## Development

```sh
python3 -m unittest test_pomo -v   # run the test suite
```

Mirroring the UI isn't needed — the timer degrades to a simple per-second
tick when stdout isn't a terminal (e.g. when piped), which also makes it easy
to drive in tests by overriding a phase's `seconds`.
