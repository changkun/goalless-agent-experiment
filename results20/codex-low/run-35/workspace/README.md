# mdgen

A tiny, dependency-free Markdown → static HTML site generator in pure Python.
No installs, no node_modules, no build pipeline — just the standard library.

## Quick start

```bash
# Build the demo site (site/ is created automatically)
python3 -m mdgen demo site

# Single file to stdout
python3 -m mdgen README.md --stdout

# Single file to a page
python3 -m mdgen post.md --title "My Post" > post.html
```

## Supported Markdown

- ATX headings `#`–`######`
- Paragraphs, ordered/unordered lists, blockquotes, horizontal rules
- Fenced code blocks with language hints
- Inline `code`, **bold**, *italic*, links, and images
- HTML is escaped by default; no raw HTML passthrough
- Output includes a responsive theme with automatic dark mode

## Layout

```
mdgen/
  __init__.py    public API
  parser.py      Markdown parsing + rendering
  cli.py         command-line interface
tests/           unittest suite
demo/            sample multi-page site
```

## Tests

```bash
python3 -m unittest discover -s tests -v
```

## Usage as a library

```python
import mdgen

snippet = mdgen.render_markdown("# Hello **world**")
page    = mdgen.render_html(open("post.md").read(), title="My Post")
```
