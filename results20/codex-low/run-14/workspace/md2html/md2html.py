"""A small, dependency-free Markdown to HTML converter."""

import re
import sys
import html

__all__ = ["convert", "main"]


def _inline(text):
    """Convert inline Markdown (emphasis, code, links) to HTML."""
    # Inline code first so Markdown inside backticks is left untouched.
    code_re = re.compile(r"`([^`]+)`")

    def code_sub(m):
        return "<code>" + html.escape(m.group(1)) + "</code>"

    parts = []
    last = 0
    for m in code_re.finditer(text):
        parts.append(_link_em(html.escape(text[last : m.start()])))
        parts.append(code_sub(m))
        last = m.end()
    parts.append(_link_em(html.escape(text[last:])))
    return "".join(parts)


def _link_em(text):
    """Replace links and emphasis within a piece of text."""
    text = re.sub(r"\[([^\]]+)\]\(([^)\s]+)\)", r'<a href="\2">\1</a>', text)
    text = re.sub(r"\*\*([^*]+)\*\*", r"<strong>\1</strong>", text)
    text = re.sub(r"\*([^*]+)\*", r"<em>\1</em>", text)
    return text


def _parse_block(block):
    block = block.rstrip("\n")

    if block.startswith("#"):
        lines = block.splitlines()
        m = re.match(r"^(#{1,6})\s+(.+)$", lines[0])
        if m:
            level = len(m.group(1))
            head = f"<h{level}>{_inline(m.group(2))}</h{level}>"
            rest = "\n".join(lines[1:])
            return head + ("\n" + _parse_block(rest) if rest.strip() else "")

    if block.startswith("```"):
        lines = block.splitlines()
        lang = lines[0][3:].strip()
        if lines[-1].strip() == "```":
            lines = lines[:-1]
        body = "\n".join(lines[1:])
        cls = f' class="language-{html.escape(lang)}"' if lang else ""
        return f"<pre><code{cls}>{html.escape(body)}</code></pre>"

    if block.startswith("> "):
        inner = "\n".join(line[2:] for line in block.splitlines() if line.startswith("> "))
        return f"<blockquote>{_parse_block(inner)}</blockquote>"

    if block.startswith("- ") or block.startswith("* "):
        items = "".join(
            f"\n<li>{_inline(line[2:])}</li>"
            for line in block.splitlines()
            if line.startswith("- ") or line.startswith("* ")
        )
        return f"<ul>{items}\n</ul>"

    if re.match(r"^\d+\.\s", block):
        items = "".join(
            f"\n<li>{_inline(re.sub(r'^\d+\.\s', '', line))}</li>"
            for line in block.splitlines()
            if re.match(r"^\d+\.\s", line)
        )
        return f"<ol>{items}\n</ol>"

    return f"<p>{_inline(block.replace(chr(10), '<br>\n'))}</p>"


def convert(markdown):
    """Convert a Markdown string to an HTML string (fragment)."""
    if markdown is None:
        return ""
    markdown = markdown.replace("\r\n", "\n").replace("\r", "\n").strip("\n")

    blocks = re.split(r"\n{2,}", markdown)
    return "\n\n".join(_parse_block(b) for b in blocks if b.strip())


def main(argv=None):
    argv = list(sys.argv[1:] if argv is None else argv)
    append_wrapper = False
    if argv and argv[0] == "--wrap":
        append_wrapper = True
        argv = argv[1:]

    if not argv:
        source = sys.stdin.read()
    else:
        with open(argv[0], encoding="utf-8") as fh:
            source = fh.read()

    body = convert(source)
    if not append_wrapper:
        sys.stdout.write(body + "\n")
        return

    title = "Output"
    sys.stdout.write(
        "<!DOCTYPE html>\n"
        "<html>\n<head>\n<meta charset=\"utf-8\">\n"
        f"<title>{title}</title>\n"
        "<style>body{font-family:system-ui,sans-serif;max-width:720px;"
        "margin:2rem auto;line-height:1.6}</style>\n"
        "</head>\n<body>\n"
        f"{body}\n"
        "</body>\n</html>\n"
    )


if __name__ == "__main__":
    main()
