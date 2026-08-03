# Pocket

A tiny, zero-dependency Python CLI for capturing notes and tasks into a single
human-readable Markdown journal.

## Install

Requires Python 3.9+. No third-party packages.

```bash
pip install -e .
```

Or run without installing:

```bash
python -m pocket.cli --help
```

The journal defaults to `~/.pocket.md`; override with `POCKET_FILE`.

## Usage

```bash
# Add a note
pocket add "buy oat milk"

# Add a task (also handy: --done for pre-completed tasks)
pocket add --task "file taxes"

# List everything (tasks only / notes only / last 3 days / first 5)
pocket list
pocket list --tasks
pocket list --notes --days 3 -n 5

# Mark done or open by 0-based index (as shown by `list`)
pocket done 0
pocket done 0 --undo

# Remove an item
pocket remove 2

# Dump the raw journal
pocket show
```

## Journal format

```markdown
# Pocket Journal

## 2026-08-03
- buy oat milk
- [ ] file taxes
- [x] ship v1
```

The file is plain Markdown, so you can edit it by hand anytime; Pocket simply
appends and re-parses.

## Development

```bash
python -m pytest tests/
```
