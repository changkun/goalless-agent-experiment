# mdx

A tiny, dependency-free Markdown → HTML converter and static site builder,
written with nothing but the Python standard library.

## Features

- Headings, paragraphs, blockquotes, horizontal rules
- Ordered and unordered lists
- Fenced code blocks with escaping
- Inline code, bold, italic
- Links and images (with optional titles)
- Escaped characters and raw HTML pass-through
- Full-document wrapping with basic styling

## Usage

Run from the `mdx` directory:

```sh
# Convert a file to an HTML fragment
PYTHONPATH=src python -m mdx convert README.md

# Full standalone document
PYTHONPATH=src python -m mdx convert README.md --full -t "My Page"

# Build an entire site from a directory
PYTHONPATH=src python -m mdx build ./site ./out
```

## Tests

```sh
PYTHONPATH=src python -m unittest discover -s tests
```
