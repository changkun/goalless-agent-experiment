# Welcome to mdgen

A tiny, **dependency-free** Markdown to static HTML site generator. Point it at
a folder of `.md` files and it produces a clean, responsive site in seconds.

## Features

- [x] Headings, paragraphs, and horizontal rules
- [x] Bold, *italic*, `inline code`, [links](https://example.com)
- [x] Ordered and unordered lists
- [x] Fenced code blocks with language highlighting hooks
- [x] Blockquotes
- [x] Images
- [x] Automatic dark mode via `prefers-color-scheme`

## A code sample

```python
def greet(name: str) -> str:
    return f"Hello, {name}!"

print(greet("mdgen"))
```

## Try it

> Great software makes a simple thing feel effortless.

1. Write some Markdown
2. Run `python -m mdgen demo site`
3. Open `site/index.html` in your browser

---

Built with mdgen.
