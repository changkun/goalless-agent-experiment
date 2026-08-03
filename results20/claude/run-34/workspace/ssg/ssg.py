#!/usr/bin/env python3
"""A tiny, zero-dependency static site generator.

Usage:
    python3 ssg.py build content/ output/
    python3 ssg.py serve output/ [port]

Content layout:
    content/
      config.yaml            # site metadata (title, url, author, tagline)
      static/...             # copied verbatim to output root
      posts/*.md             # blog posts with YAML frontmatter
      pages/*.md             # standalone pages (index/about/contact)

Each markdown file may start with a YAML frontmatter block:

    ---
    title: My Post
    date: 2026-08-01
    tags: [python, web]
    draft: false
    ---

Outputs:
    output/index.html        # page listing, or built from pages/index.md
    output/posts/<slug>/     # rendered post
    output/tags/<tag>/       # per-tag index
    output/rss.xml           # Atom feed
    output/search.json       # client-side search index
"""

from __future__ import annotations

import html
import json
import mimetypes
import os
import re
import shutil
import sys
from datetime import datetime, timezone
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Dict, List

import markdown as md

# Minimal YAML-ish frontmatter parser.
_FM_BLOCK = re.compile(r"\A---\s*\n(.*?)\n---\s*\n", re.DOTALL)


def parse_frontmatter(text: str) -> tuple[dict, str]:
    """Split a file into (metadata dict, remaining markdown)."""
    meta: dict = {}
    m = _FM_BLOCK.match(text)
    if not m:
        return meta, text
    for line in m.group(1).splitlines():
        if ":" not in line:
            continue
        key, _, value = line.partition(":")
        key = key.strip()
        value = value.strip()
        if value.startswith("[") and value.endswith("]"):
            value = [v.strip().strip("'\"") for v in value[1:-1].split(",") if v.strip()]
        elif value.lower() in ("true", "false"):
            value = value.lower() == "true"
        else:
            value = value.strip("'\"")
        meta[key] = value
    return meta, text[m.end():]


def slugify(text: str) -> str:
    text = text.lower().strip()
    text = re.sub(r"[^a-z0-9]+", "-", text)
    return text.strip("-") or "untitled"


def render_template(tpl: str, **ctx) -> str:
    """Render a tiny template: {{ var }} and {% for x in list %}...{% endfor %}."""
    def var_repl(m):
        key = m.group(1).strip()
        if "." in key:
            obj, attr = key.split(".", 1)
            val = ctx.get(obj, {})
            if isinstance(val, dict):
                val = val.get(attr)
        else:
            val = ctx.get(key)
        if val is None:
            return ""
        if isinstance(val, bool):
            return "true" if val else "false"
        return str(val)

    def for_repl(m):
        header, body = m.group(1), m.group(2)
        var = header.split()[1]
        items = ctx.get(header.split(" in ")[1].strip(), []) if " in " in header else []
        return "".join(render_template(body, **{**ctx, var: item}) for item in items)

    tpl = re.sub(r"\{%\s*for\s+(.+?)\s*%\}(.*?)\{%\s*endfor\s*%\}", for_repl, tpl, flags=re.DOTALL)
    tpl = re.sub(r"\{\{\s*(.*?)\s*\}\}", var_repl, tpl)
    return tpl


class Site:
    def __init__(self, content_dir: Path, output_dir: Path):
        self.content = content_dir
        self.out = output_dir
        self.config = self._load_config()
        self.template = self._load_template()
        self.posts: List[Dict] = []

    # --- loading --------------------------------------------------------
    def _load_config(self) -> dict:
        cfg_path = self.content / "config.yaml"
        cfg = {"title": "Untitled", "url": "https://example.com",
               "author": "Anonymous", "tagline": ""}
        if cfg_path.exists():
            text = cfg_path.read_text()
            local, _ = parse_frontmatter("---\n" + text + "\n---\n")
            cfg.update(local)
        return cfg

    def _load_template(self) -> str:
        tpl_path = self.content / "template.html"
        default = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{{ title }}</title>
<link rel="stylesheet" href="{{ css }}">
<link rel="alternate" type="application/atom+xml" href="{{ base_url }}/rss.xml" title="{{ site_title }}">
</head>
<body>
<header class="site-header">
  <a class="brand" href="{{ base_url }}/">{{ site_title }}</a>
  <nav><a href="{{ base_url }}/">Home</a> <a href="{{ base_url }}/about/">About</a></nav>
</header>
<main>
{{ body }}
</main>
<footer>© {{ year }} {{ site_author }}</footer>
</body>
</html>"""
        if tpl_path.exists():
            return tpl_path.read_text()
        return default

    # --- build ----------------------------------------------------------
    def build(self) -> None:
        if self.out.exists():
            shutil.rmtree(self.out)
        self.out.mkdir(parents=True)

        # Static assets first.
        static = self.content / "static"
        if static.exists():
            shutil.copytree(static, self.out, dirs_exist_ok=True)

        self._write_theme_css()
        self._build_posts()
        self._build_pages()
        self._build_tag_indices()
        self._build_feed()
        self._build_search_index()

    def _render(self, body_html: str, title: str = "") -> str:
        ctx = {
            "site_title": self.config.get("title", ""),
            "site_tagline": self.config.get("tagline", ""),
            "site_author": self.config.get("author", ""),
            "base_url": self.config.get("url", "").rstrip("/"),
            "title": f"{title} — {self.config.get('title','')}" if title else self.config.get("title", ""),
            "body": body_html,
            "css": "/style.css",
            "year": datetime.now().year,
        }
        return render_template(self.template, **ctx)

    def _write_theme_css(self) -> None:
        css = self.content / "static" / "style.css"
        if css.exists() and css.stat().st_size > 0:
            return  # author supplied their own theme
        default_css = """\
:root{--bg:#ffffff;--fg:#1a1a1a;--accent:#3457d5;--muted:#6b7280;--border:#e5e7eb;
--code-bg:#f6f8fa;--maxw:720px}
*{box-sizing:border-box}
body{margin:0;font:17px/1.7 system-ui,-apple-system,"Segoe UI",Roboto,sans-serif;
color:var(--fg);background:var(--bg);-webkit-font-smoothing:antialiased}
.site-header{max-width:var(--maxw);margin:0 auto;padding:2rem 1.25rem 0;display:flex;
justify-content:space-between;align-items:baseline;flex-wrap:wrap;gap:.5rem}
.brand{font-size:1.35rem;font-weight:700;color:var(--fg);text-decoration:none;letter-spacing:-.02em}
nav a{color:var(--muted);text-decoration:none;margin-left:1rem;font-size:.95rem}
nav a:hover{color:var(--accent)}
main{max-width:var(--maxw);margin:0 auto;padding:1.5rem 1.25rem 3rem}
a{color:var(--accent);text-decoration-thickness:.08em;text-underline-offset:2px}
a:hover{text-decoration:underline}
h1,h2,h3,h4{line-height:1.25;letter-spacing:-.02em;margin:1.6em 0 .5em}
h1{font-size:2rem;margin-top:.75em}
h2{font-size:1.5rem;padding-bottom:.3em;border-bottom:1px solid var(--border)}
pre{background:var(--code-bg);padding:1rem;border-radius:8px;overflow-x:auto;font-size:.9rem}
pre code{background:none;padding:0}
code{background:var(--code-bg);padding:.15em .35em;border-radius:4px;font-size:.88em;
font-family:ui-monospace,SFMono-Regular,Menlo,Consolas,monospace}
blockquote{margin:1.5em 0;padding:.25em 0 .25em 1.25em;border-left:4px solid var(--border);
color:var(--muted)}
img{max-width:100%;height:auto;border-radius:8px}
table{border-collapse:collapse;width:100%;margin:1.5em 0;font-size:.95rem}
th,td{border:1px solid var(--border);padding:.5em .75em;text-align:left}
th{background:var(--code-bg)}
hr{border:none;border-top:1px solid var(--border);margin:2em 0}
ul,ol{padding-left:1.4em}
article.post-list{margin-bottom:2.2rem}
.post-meta{color:var(--muted);font-size:.85rem;margin:.2rem 0 .8rem;font-variant-numeric:tabular-nums}
.tag{display:inline-block;background:var(--code-bg);border-radius:999px;padding:.1em .7em;
font-size:.75rem;color:var(--accent);margin-right:.35rem;text-decoration:none}
footer{max-width:var(--maxw);margin:0 auto;padding:1.5rem 1.25rem 3rem;color:var(--muted);
font-size:.85rem;border-top:1px solid var(--border)}
.search{margin-top:1.5rem}
.search input[type=search]{width:100%;max-width:24rem;padding:.5rem .8rem;border:1px solid var(--border);
border-radius:8px;font:inherit;color:var(--fg);background:var(--code-bg)}
.search input[type=search]:focus{outline:2px solid var(--accent);outline-offset:1px;background:var(--bg)}
#search-results{margin-top:1rem}
footer .search h2{font-size:1rem;margin:.6em 0 .2em}
@media (prefers-color-scheme:dark){:root{--bg:#0f1115;--fg:#e6e6e6;--muted:#9aa0a6;
--border:#2a2f38;--code-bg:#171a21;--accent:#7aa2ff}}
"""
        (self.out / "style.css").write_text(default_css)


    def _build_posts(self) -> None:
        posts_dir = self.content / "posts"
        if not posts_dir.exists():
            return
        for path in sorted(posts_dir.glob("*.md")):
            meta, body = parse_frontmatter(path.read_text())
            if meta.get("draft"):
                continue
            slug = meta.get("slug") or slugify(path.stem)
            date = str(meta.get("date", ""))[:10]
            tags = meta.get("tags", [])
            if isinstance(tags, str):
                tags = [t.strip() for t in tags.split(",") if t.strip()]
            body_html = md.convert(body)
            record = {
                "slug": slug,
                "title": meta.get("title", path.stem),
                "date": date,
                "tags": tags,
                "url": f"/posts/{slug}/",
                "excerpt": _excerpt(body_html),
            }
            self.posts.append(record)
            html = self._render(body_html, record["title"])
            out = self.out / "posts" / slug
            out.mkdir(parents=True, exist_ok=True)
            (out / "index.html").write_text(html)
        self.posts.sort(key=lambda p: p.get("date", ""), reverse=True)

    def _build_pages(self) -> None:
        pages_dir = self.content / "pages"
        index_path = Path(self.content) / "pages" / "index.md"
        # Index page.
        if index_path.exists():
            meta, body = parse_frontmatter(index_path.read_text())
            (self.out / "index.html").write_text(self._render(md.convert(body)))
        else:
            list_html = self._render_post_list(self.posts, intro=self.config.get("tagline", ""))
            (self.out / "index.html").write_text(self._render(list_html))
        # Other pages.
        if pages_dir.exists():
            for path in sorted(pages_dir.glob("*.md")):
                if path.name == "index.md":
                    continue
                meta, body = parse_frontmatter(path.read_text())
                slug = slugify(path.stem)
                out = self.out / slug
                out.mkdir(parents=True, exist_ok=True)
                title = meta.get("title", path.stem)
                (out / "index.html").write_text(self._render(md.convert(body), title))

    def _render_post_list(self, posts: List[Dict], intro: str = "") -> str:
        parts = [f"<p class='intro'>{html.escape(intro)}</p>" if intro else ""]
        for p in posts:
            tags_html = "".join(
                f'<a class="tag" href="/tags/{html.escape(t)}/">{html.escape(t)}</a>'
                for t in p["tags"]
            )
            parts.append(
                f"<article class='post-list'><h2><a href='{p['url']}'>{html.escape(p['title'])}</a></h2>"
                f"<div class='post-meta'>{p['date']}{(' · ' + tags_html) if tags_html else ''}</div>"
                f"<p>{p['excerpt']}</p></article>"
            )
        if not parts or all(not x for x in parts):
            parts.append("<p>No posts yet.</p>")
        return "\n".join(x for x in parts if x)

    def _build_tag_indices(self) -> None:
        tag_map: Dict[str, List[Dict]] = {}
        for p in self.posts:
            for t in p["tags"]:
                tag_map.setdefault(t, []).append(p)
        tags_dir = self.out / "tags"
        for tag, posts in tag_map.items():
            out = tags_dir / slugify(tag)
            out.mkdir(parents=True, exist_ok=True)
            list_html = f"<h1>#{html.escape(tag)}</h1>" + self._render_post_list(posts)
            (out / "index.html").write_text(self._render(list_html, tag))
        # Link back from home.
        index = self.out / "index.html"
        if index.exists():
            html_text = index.read_text()
            tag_cloud = " ".join(
                f'<a class="tag" href="/tags/{slugify(t)}/">#{html.escape(t)}</a>'
                for t in sorted(tag_map)
            )
            if tag_cloud:
                inject = f"\n<div class='tag-cloud'><strong>Tags:</strong> {tag_cloud}</div>"
                html_text = html_text.replace("</main>", inject + "</main>")
                index.write_text(html_text)

    def _build_feed(self) -> None:
        base = self.config.get("url", "").rstrip("/")
        entries = []
        for p in self.posts:
            entries.append(
                "  <entry>\n"
                f"    <title>{html.escape(p['title'])}</title>\n"
                f"    <link href='{base}{p['url']}'/>\n"
                f"    <id>{base}{p['url']}</id>\n"
                f"    <updated>{p['date']}T00:00:00Z</updated>\n"
                f"    <content type='html'>{html.escape(p['excerpt'])}</content>\n"
                "  </entry>"
            )
        feed = (
            "<?xml version='1.0' encoding='utf-8'?>\n"
            f"<feed xmlns='http://www.w3.org/2005/Atom'>\n"
            f"  <title>{html.escape(self.config.get('title',''))}</title>\n"
            f"  <id>{base}/</id>\n"
            f"  <link href='{base}/rss.xml' rel='self'/>\n"
            f"  <updated>{datetime.now(timezone.utc).isoformat()}</updated>\n"
            f"  <author><name>{html.escape(self.config.get('author',''))}</name></author>\n"
            + "\n".join(entries)
            + "\n</feed>\n"
        )
        (self.out / "rss.xml").write_text(feed)

    def _build_search_index(self) -> None:
        index = [
            {"title": p["title"], "url": p["url"], "date": p["date"],
             "tags": p["tags"], "excerpt": p["excerpt"]}
            for p in self.posts
        ]
        (self.out / "search.json").write_text(json.dumps(index, ensure_ascii=False))


def _excerpt(body_html: str, limit: int = 200) -> str:
    text = re.sub(r"<[^>]+>", " ", body_html)
    text = re.sub(r"\s+", " ", text).strip()
    if len(text) > limit:
        return text[:limit].rstrip() + "…"
    return text


# --- server ---------------------------------------------------------------

class QuietHandler(SimpleHTTPRequestHandler):
    def log_message(self, *args):  # keep the console clean
        pass


def serve(directory: Path, port: int = 8000) -> None:
    directory = directory.resolve()  # SimpleHTTPRequestHandler needs an absolute path
    os.chdir(directory)
    handler = lambda *a, **kw: QuietHandler(*a, directory=str(directory), **kw)
    httpd = ThreadingHTTPServer(("127.0.0.1", port), handler)
    print(f"Serving {directory} at http://127.0.0.1:{port}/  (Ctrl+C to stop)")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nStopped.")


def main(argv: List[str]) -> int:
    if len(argv) < 2:
        print(__doc__)
        return 1
    cmd = argv[1]
    if cmd == "build":
        if len(argv) < 4:
            print("usage: ssg.py build <content-dir> <output-dir>")
            return 1
        site = Site(Path(argv[2]), Path(argv[3]))
        site.build()
        print(f"Built {len(site.posts)} posts -> {site.out}")
        return 0
    if cmd == "serve":
        if len(argv) < 3:
            print("usage: ssg.py serve <output-dir> [port]")
            return 1
        port = int(argv[3]) if len(argv) > 3 else 8000
        serve(Path(argv[2]), port)
        return 0
    print(__doc__)
    return 1


if __name__ == "__main__":
    sys.exit(main(sys.argv))
