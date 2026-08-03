# mdterm

A tiny, dependency-free Markdown → terminal renderer built on the Python
standard library. It adds ANSI colors for headings, code, links, and lists so
you can pretty-print Markdown directly in your terminal.

## Usage

    python3 mdterm.py notes.md
    cat notes.md | python3 mdterm.py

Color levels:

    python3 mdterm.py --color none notes.md   # plain text
    python3 mdterm.py --color min  notes.md   # still formats inline markup
    python3 mdterm.py --color full notes.md   # full colors (default)

## Supported syntax

- `#`–`######` headings
- bold, italic, `inline code`, and images/links
- fenced code blocks (``` and ~~~) with an optional language label
- unordered (`-`, `*`, `+`) and ordered lists
- blockquotes (`>`)
- horizontal rules

## Tests

    python3 -m unittest test_mdterm.py
