# pnotes

A tiny, **dependency-free** notes & todo manager for the terminal. Built on the
Python standard library only, so it runs anywhere Python 3.10+ runs.

Notes are stored as plain-text files under a single root directory
(`~/.pnotes` by default), which makes them transparent, grep-able, and easy to
sync with git or Dropbox.

## Install / run

```bash
# from the repo directory — no install needed:
python3 pnotes.py --help

# optional: drop on your PATH
chmod +x pnotes.py
ln -s "$(pwd)/pnotes.py" ~/.local/bin/pnotes
```

Point it at a custom root with `--dir` or the `PNOTES_DIR` environment variable
(handy for testing or for keeping separate work/personal notes).

## Usage

```bash
# Create a note with todo items
pnotes add -t "Groceries" "Milk" "Bread #errand" -d 2026-12-01

# Interactive mode (prompts for a title and items)
pnotes add -i

# List everything (overdue first, then by due date)
pnotes list

# Only notes happening today / filtered by tag
pnotes list --do
pnotes list --tag errand

# Show a note with its items
pnotes show groceries

# Mark an item complete
pnotes done groceries 1

# Tag tally (counts open items, ignores completed)
pnotes tags

# Quick totals
pnotes stats

# Delete a note
pnotes rm groceries
```

## Data model

```
~/.pnotes/
  index                 # sorted header lines: slug\t<due|->
  groceries/
    meta.json           # {"title", "due", "created"}
    todos.txt           # [ ] / [x] / [!] item, one per line
```

- `[ ]` open, `[x]` done, `[!]` important/flagged.
- Tags are just `#word` tokens inside an item's text — `tags` tallies them.

## Tests

```bash
python3 test_pnotes.py          # stdlib-only runner
# or
python3 -m pytest               # if you have pytest
```

## Design notes

- **Zero dependencies** and ASCII-safe output, so it works in minimal
  environments and copy-pastes cleanly.
- The per-note files are the **source of truth**; the `index` is opportunistic
  and rebuilt on writes, so a missing/corrupt index never hides your data.
- Items are addressed by 1‑based line number in `show`/`done`, keeping the
  storage format trivially human-editable.
