# tmd

A tiny, dependency-free Markdown → colorized terminal renderer, written in
pure Python 3. Handy for reading `README.md` and docs straight from the shell.

## Usage

```sh
./tmd.py README.md     # render a file
cat foo.md | ./tmd.py  # or pipe via stdin
./tmd.py --no-color    # force plain output (also automatic when piped)
```

## Supported

- `#`–`######` headings
- `**bold**`, `*italic*`, `` `code` ``
- `[links](url)`
- `-`/`*` unordered and `1.` ordered lists
- `> blockquotes`
- ` ``` fenced code blocks ``
- `---` horizontal rules
- paragraphs

## Notes

- Colors are auto-disabled when stdout isn't a TTY (e.g. piped into `less`).
- No third-party dependencies; just Python 3.7+.
