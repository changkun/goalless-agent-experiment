# scraps

A tiny, zero-dependency note-taking CLI written in pure Python.

## Usage

```bash
scraps add "buy oat milk"
scraps list
scraps list --search oat
scraps remove 1
```

Notes are stored as JSON in `~/.scraps.json`, or wherever `SCRAPS_FILE`
points to.

## Run

```bash
python3 scraps/scraps.py add "hello"
python3 -m unittest discover -s scraps
```
