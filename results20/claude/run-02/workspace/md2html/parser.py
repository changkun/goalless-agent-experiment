"""Block-level Markdown parsing.

`parse` turns a string of Markdown into a tree of block nodes. Each node is
either a simple scalar-bearing block (heading, paragraph, code, hr) or a
container (blockquote, list) whose children are more blocks.

The parser works on a flat list of lines. The entry point `_parse_blocks`
scans a run of sibling blocks and recurses whenever it opens a container
element, so nesting is handled naturally. A container collects the raw lines
that belong to it, strips its own marker, and recurses on the result.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import List, Optional, Tuple

# --- node types -------------------------------------------------------------

@dataclass
class Heading:
    level: int
    text: str


@dataclass
class Paragraph:
    lines: List[str] = field(default_factory=list)


@dataclass
class CodeBlock:
    code: str
    info: str = ""


@dataclass
class Hr:
    pass


@dataclass
class Blockquote:
    children: List["BlockNode"] = field(default_factory=list)


@dataclass
class ListItem:
    children: List["BlockNode"] = field(default_factory=list)


@dataclass
class ListBlock:
    ordered: bool
    items: List[ListItem] = field(default_factory=list)


BlockNode = (Heading, Paragraph, CodeBlock, Hr, Blockquote, ListItem, ListBlock)

# --- regexes ----------------------------------------------------------------

ATX = re.compile(r"^ {0,3}(#{1,6})(?:[ \t]+(.*?))?[ \t]*#*[ \t]*$")
FENCE = re.compile(r"^ {0,3}(`{3,}|~{3,})(.*)$")
QUOTE = re.compile(r"^ {0,3}> ?")
UL_MARKER = re.compile(r"^ {0,3}([-*+])([ \t]|$)")
OL_MARKER = re.compile(r"^ {0,3}(\d{1,9})([.)])([ \t]|$)")

# --- helpers ----------------------------------------------------------------

def is_blank(line: str) -> bool:
    return line.strip() == ""


def indent(line: str) -> int:
    """Width of leading whitespace (tabs count as 4 columns)."""
    w = 0
    for ch in line:
        if ch == " ":
            w += 1
        elif ch == "\t":
            w += 4 - (w % 4)
        else:
            break
    return w


def is_hr(line: str) -> bool:
    """A thematic break: 3+ of a single char chosen from -*_ with only
    whitespace between. Must not collide with a list marker (`- item`)."""
    s = line.lstrip()
    cs = [c for c in s if not c.isspace()]
    if len(cs) < 3:
        return False
    if not all(c in "-*_" for c in cs):
        return False
    return len(set(cs)) == 1


def ordered_or_unordered(line: str) -> Optional[bool]:
    """True if ordered item, False if unordered item, None if neither."""
    if OL_MARKER.match(line):
        return True
    if UL_MARKER.match(line):
        return False
    return None


def is_item(line: str, ordered: bool) -> bool:
    return ordered_or_unordered(line) is ordered


# --- parser -----------------------------------------------------------------

def parse(text: str) -> List[BlockNode]:
    return _parse_blocks(text.split("\n"), 0, text.count("\n") + 1)[0]


def _parse_blocks(lines: List[str], i: int, end: int) -> Tuple[List[BlockNode], int]:
    blocks: List[BlockNode] = []
    while i < end:
        line = lines[i]

        if is_blank(line):
            i += 1
            continue

        if is_hr(line):
            blocks.append(Hr())
            i += 1
            continue

        ul = UL_MARKER.match(line)
        ol = OL_MARKER.match(line)

        # ATX heading (a lone `#` is a heading even without a space)
        m = ATX.match(line)
        if m and ul is None and ol is None:
            blocks.append(Heading(len(m.group(1)), (m.group(2) or "").strip()))
            i += 1
            continue

        # fenced code
        mf = FENCE.match(line)
        if mf:
            block, i = _consume_fence(lines, i, end, mf.group(1), mf.group(2).strip())
            blocks.append(block)
            continue

        # blockquote
        if QUOTE.match(line):
            inner: List[str] = []
            while i < end:
                ln = lines[i]
                mq = QUOTE.match(ln)
                if mq is None:
                    break
                inner.append(ln[mq.end():])
                i += 1
            children, _ = _parse_blocks(inner, 0, len(inner))
            blocks.append(Blockquote(children))
            continue

        # list
        if ul or ol:
            block, i = _parse_list(lines, i, end, bool(ol))
            blocks.append(block)
            continue

        # indented code block
        if indent(line) >= 4:
            code_lines = [line[4:]]
            i += 1
            while i < end:
                ln = lines[i]
                if is_blank(ln):
                    code_lines.append("")
                    i += 1
                    continue
                if indent(ln) >= 4:
                    code_lines.append(ln[4:])
                    i += 1
                    continue
                break
            while code_lines and code_lines[-1] == "":
                code_lines.pop()
            blocks.append(CodeBlock("\n".join(code_lines)))
            continue

        # paragraph — consume consecutive owned lines
        para_lines = [line]
        i += 1
        while i < end:
            ln = lines[i]
            if is_blank(ln) or is_hr(ln) or ATX.match(ln) or QUOTE.match(ln) \
               or FENCE.match(ln) or UL_MARKER.match(ln) or OL_MARKER.match(ln) \
               or indent(ln) >= 4:
                break
            para_lines.append(ln)
            i += 1
        blocks.append(Paragraph(para_lines))

    return blocks, i


def _consume_fence(lines: List[str], i: int, end: int, fence: str,
                   info: str) -> Tuple[CodeBlock, int]:
    """From the opening fence at line i, consume until the matching close.
    Returns the code block and the index past the close."""
    buf: List[str] = []
    i += 1
    while i < end:
        ln = lines[i]
        m = FENCE.match(ln)
        if m and m.group(1)[0] == fence[0] and len(m.group(1)) >= len(fence) \
           and is_blank(m.group(2)):
            i += 1
            return CodeBlock("\n".join(buf), info), i
        buf.append(ln)
        i += 1
    return CodeBlock("\n".join(buf), info), i


def _parse_list(lines: List[str], i: int, end: int, ordered: bool) -> Tuple[ListBlock, int]:
    block = ListBlock(ordered)
    while i < end:
        ln = lines[i]

        if is_blank(ln):
            # Loose list: skip blanks, continue only if a fresh same-kind
            # item follows.
            j = i
            while j < end and is_blank(lines[j]):
                j += 1
            if j < end and is_item(lines[j], ordered):
                i = j
                continue
            break

        if not is_item(ln, ordered):
            break

        m = (OL_MARKER if ordered else UL_MARKER).match(ln)
        marker_end = m.end()
        # The marker includes up to 3 leading spaces; content begins at the
        # column of the first non-space char after the marker.
        content_col = indent(ln[:marker_end]) + marker_end
        content = [ln[marker_end:]]
        i += 1

        # continuation lines belonging to this item: anything indented to the
        # content column (covers wrapped text, nested blocks, nested lists)
        while i < end:
            ln2 = lines[i]
            if is_blank(ln2):
                break
            ind = indent(ln2)
            if ind >= content_col:
                content.append(ln2[content_col:])
                i += 1
                continue
            break

        children, _ = _parse_blocks(content, 0, len(content))
        block.items.append(ListItem(children))
    return block, i
