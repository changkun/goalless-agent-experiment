# standup.py

A tiny CLI for daily standup notes.

## Usage

```bash
python3 standup.py log "Fixed auth bug in login flow"
python3 standup.py log           # interactive multi-line input
python3 standup.py list -n 5 --show
python3 standup.py search "auth"
```

Notes are stored as `YYYY-MM-DD.md` files in `~/.standup/` by default.
Use `--dir <path>` to override.
