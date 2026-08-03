# focustrack

A tiny focus-session tracker. Records focus sessions (project, tags, notes) in a
local JSON file, then lets you review how you actually spend your time — by day,
week, or an arbitrary trailing window — and export the day as Markdown.

No dependencies beyond the Python standard library (3.9+).

## Install / run

```bash
# make it executable and put it on your PATH:
chmod +x focustrack.py
ln -s "$PWD/focustrack.py" ~/.local/bin/focustrack
```

Or just run it in place: `python3 focustrack.py ...`

## Quick start

```bash
# Start an interactive timer — Ctrl+C ends it and saves the session.
focustrack start --project "Docs" --tag writing --tag research

# Record a session whose length you already know.
focustrack add --minutes 45 --project "Docs" --tag writing --note "draft"

# Look back.
focustrack today            # today's sessions
focustrack week             # this week (Mon → today)
focustrack list --limit 10  # recent sessions
focustrack summary --days 7 # per-project / per-day / per-tag breakdown
focustrack export -o s.md   # the day as Markdown
```

## Store

Sessions live in `~/.focustrack.json` by default (override with `--db`). Each
record looks like:

```json
{
  "id": 1,
  "project": "Docs",
  "tags": ["writing", "research"],
  "note": "draft outline",
  "started": "2026-08-03T18:52:00",
  "ended": "2026-08-03T19:37:00",
  "minutes": 45
}
```

Edit the file freely — missing/partial fields are tolerated on read.

## Development

```bash
python3 -m py_compile focustrack.py   # syntax check
```
