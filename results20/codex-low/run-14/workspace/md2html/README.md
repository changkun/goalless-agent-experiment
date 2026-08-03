# md2html

A small, dependency-free Markdown → HTML converter written in Python.

## Features
- Headings `#` through `######`
- Paragraphs, unordered (`-`) and ordered (`1.`) lists
- Blockquotes
- Fenced code blocks (with language class)
- Inline: `**bold**`, `*em*`, `` `code` ``, `[text](url)`
- HTML escaping of raw text

## Usage
```bash
# Read from a file
python3 md2html.py input.md

# Read from stdin
cat input.md | python3 md2html.py

# Wrap output in a full HTML document
python3 md2html.py --wrap input.md > output.html
```

## API
```python
from md2html import convert
html = convert("# Hello *world*")
```

## Tests
```bash
python3 -m unittest test_md2html -v
```
