# tnote

A tiny, dependency-free notes/TODO manager for the terminal. Entries are stored
as plain Markdown, typically in `~/.tnote.md`.

## Usage

```sh
./tnote add "ship the release"      # add a pending entry
./tnote list                         # show pending entries
./tnote list --all                   # show pending + done
./tnote done 1                       # mark entry 1 done
./tnote rm 2                         # remove entry 2
./tnote stats                        # pending / done / total
```

Use `--file <path>` (or the `TNOTE_FILE` env var) to point at a different notes
file.

The on-disk format is plain Markdown, so you can also just open and edit the
file in any editor:

```md
- [ ] a pending task
- [x] a completed task
```

## Install

Copy `tnote` somewhere on your `PATH`:

```sh
install -m 755 tnote ~/.local/bin/tnote
```

Requires Python 3.6+ (standard library only).
