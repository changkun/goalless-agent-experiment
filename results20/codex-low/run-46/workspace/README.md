# md2html

A small, dependency-free Markdown-to-HTML converter written in Python (stdlib
only). It renders a Markdown document as an HTML fragment.

## Features

- Headings, paragraphs, and horizontal rules
- Unordered and ordered lists
- Fenced code blocks with optional language class
- Blockquotes
- Inline `**bold**`, `*italic*`, `` `code` ``, `[links](url)`, and `![images](url)`
- HTML escaping of user content for safe output

## Install

```bash
pip install .
```

Or run it without installing:

```bash
python -m md2html README.md
```

## Usage

As a library:

```python
from md2html import convert

html = convert("# Hello\n\n**world**")
print(html)
# <h1>Hello</h1>
# <p><strong>world</strong></p>
```

As a CLI:

```bash
# Read a file
md2html input.md

# Read from stdin
cat input.md | md2html

# Write to a file
md2html input.md -o output.html
```

## Tests

```bash
python -m unittest discover -s tests
```
