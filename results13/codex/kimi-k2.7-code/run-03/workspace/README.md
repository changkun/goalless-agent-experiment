# dnote

A tiny command-line journal.

## Install

```bash
chmod +x dnote
# Optional: put it on PATH
ln -s "$PWD/dnote" ~/.local/bin/dnote
```

## Usage

```bash
dnote write "Finished the draft"
dnote write              # writes an empty timestamp entry
dnote show               # today's notes
dnote show 2026-07-01    # notes for a specific date
dnote list               # all dates with notes
```

Notes are stored as `~/.dnote/YYYY-MM-DD.md`.
