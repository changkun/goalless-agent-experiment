# tiny-ssg

A zero-dependency static site generator in Python 3.12 — **stdlib only**, no
`node_modules`, no `gemfile`, no build step beyond one command.

## Quick start

```bash
python3 ssg.py build content/ output/
python3 ssg.py serve output/ [port]     # http://127.0.0.1:8000
```

## What it does

- Renders `posts/*.md` and `pages/*.md` (with YAML-ish frontmatter) to HTML
- Generates a post index, per-tag archives, an Atom feed, and `search.json`
- Ships a dependency-free Markdown → HTML converter (`markdown.py`) supporting
  headings, paragraphs, lists, blockquotes, fenced code, tables, HRs, and the
  common inline styles
- Includes a clean default theme (light/dark auto), customizable via
  `content/template.html` and `content/static/style.css`
- Has no build-time network access and produces no `.pyc` output into `content/`

### Sample content
`content/` holds a small working site — three posts (one tagged draft, correctly
excluded), an about page, and a dot for image handling.

## Layout

```
content/
  config.yaml       site metadata (title, url, author, tagline)
  template.html     optional base template (Jinja-ish {{ var }} / {% for %})
  static/...        copied verbatim to output root
  posts/*.md        blog posts with frontmatter
  pages/*.md        index + standalone pages
output/
  index.html        post listing (or pages/index.md)
  posts/<slug>/     rendered post
  tags/<tag>/       per-tag index
  rss.xml, search.json
```

## Notes

- Drafts (`draft: true`) are skipped at build time.
- Dates sort posts; frontmatter supports `slug`, `title`, `date`, `tags`, `draft`.
- Tested under Python 3.12 with only the standard library.
