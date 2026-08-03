# mdgen

A small, dependency-free Markdown-to-HTML converter with a CLI and a library API.

## Features

- ATX headings (`#`..`######`)
- Ordered and unordered lists with nesting
- Blockquotes and fenced code blocks
- Inline `code`, **bold**, *italic*, [links](), and images
- HTML escaping of user-supplied text

## Library

```python
from mdgen import to_html

html = to_html("# Hello, world!")
```

## CLI

Convert a single file to HTML on stdout:

```bash
python -m mdgen example/index.md
```

Build a whole directory of `.md` files into HTML:

```bash
python -m mdgen example -o example/dist
```

## Tests

```bash
python -m unittest discover -s tests -v
```
