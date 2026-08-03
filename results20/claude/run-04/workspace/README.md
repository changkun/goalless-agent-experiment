# memo

A tiny, zero-dependency, tagged journal stored as a single JSON file. No cloud,
no database, no install beyond Python's standard library.

## Run it

```bash
python3 -m memo init                                  # create ./memo.json (MEMO_PATH to relocate)
python3 -m memo add "Buy oat milk #errands #today"
python3 -m memo add "Write launch email #work/launch"
python3 -m memo ls                                    # all memos, newest first
python3 -m memo search errands today                  # AND semantics: has all tags
python3 -m memo search --prefix work                  # tag prefix match (work → work/launch)
python3 -m memo tags                                  # all tags, most frequent first
python3 -m memo rm 7490123282000117761                # remove by id
```

Or install it as a command: `pip install -e .` gives you a `memo` binary.

## Design

- **Persistence** — a flat list of `{id, ts, text, tags}` in one JSON file.
  Writes are atomic (temp file + rename), so a crash never corrupts the store.
- **Tags** — any `#tag` in the text is extracted at write time (`#work/launch`
  works as a hierarchy). Search is AND across tags, newest-first.
- **Prefix matching** — `search --prefix work` matches `#work`, `#work/deep`,
  `#work/launch`, letting tags behave like a lightweight tree.

The core (`memo/core.py`) has no CLI or I/O coupling beyond the file path, and
is fully covered by `tests/test_core.py` (14 tests, all passing).

## Layout

```
memo/
  core.py        storage, tag parsing, search  (library, no I/O beyond the store)
  __main__.py    argparse CLI
  __init__.py
tests/test_core.py
```
