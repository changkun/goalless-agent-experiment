# md2html

A small, dependency-free **Markdown → HTML** converter, written from scratch
in pure Python (stdlib only, Python 3.9+). No `markdown`, no `mistune`, no
network — just a single package and a CLI.

## Why

Most one-liner Markdown libraries are wrappers around the same two or three C
extensions. This one is a clean-room implementation you can read top to bottom
in a few minutes: a line-based block parser (`parser.py`) and a left-to-right
inline tokenizer (`render.py`). It's a good starting point if you want to
actually *understand* how Markdown parsing works, or if you need a tiny
converter you can vendor and trust.

## Usage

As a library:

```python
from md2html import convert

html = convert("# Hello *world*")
# <h1>Hello <em>world</em></h1>
```

As a CLI:

```bash
python -m md2html README.md > README.html
echo '# Hi' | python -m md2html
python -m md2html -o out.html README.md
```

## Supported syntax

| Construct | Markdown | Output |
|---|---|---|
| Headings | `# H1` … `###### H6` | `<h1>` … `<h6>` |
| Paragraphs | consecutive text lines | `<p>` |
| Emphasis / strong | `*x*`, `_x_`, `**x**`, `***x***` | `<em>`, `<strong>` |
| Inline code | `` `x` `` | `<code>` |
| Fenced code | ```` ```lang ```` … ```` ``` ```` | `<pre><code class="language-lang">` |
| Indented code | 4-space indent | `<pre><code>` |
| Links | `[t](url "title")` | `<a href="…" title="…">` |
| Images | `![alt](src)` | `<img src="…" alt="…">` |
| Autolinks | bare `https://…` | `<a href="…">` |
| Blockquotes | `> text` | `<blockquote>` |
| Lists | `- item`, `1. item`, nested | `<ul>` / `<ol>` / `<li>` |
| Thematic break | `---`, `***`, `___` | `<hr>` |

Content is HTML-escaped by default (an angle bracket in your text never
becomes a tag).

## Project layout

```
md2html/
  __init__.py     public API (convert)
  parser.py       block-level parsing -> node tree
  render.py       node tree -> HTML (inline tokenizer)
  convert.py      public conversion function
  __main__.py     CLI entry point
tests/
  test_md2html.py  27 tests
```

## Testing

```bash
python -m unittest discover -s tests -v
```

## Limitations

This is a deliberately small converter, not a CommonMark implementation. It
does **not** handle: reference-style links, HTML blocks, tables, task lists,
footnotes, or the full emphasis/backtick disambiguation rules. It aims for
correct output on the common path, not edge-case conformance.
