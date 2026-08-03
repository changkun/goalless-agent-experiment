#!/usr/bin/env python3
"""pnotes — a tiny, dependency-free notes & todo manager for the terminal.

Notes are stored as plain-text files, one directory per note. Each note can
have a title, an optional due date, and tagged todo items. State lives in a
single root directory (default: ~/.pnotes), so everything stays transparent,
greppable, and trivially syncable with git or Dropbox.

Commands:
    add        Create a note (interactively, or with -t/--title and
               positional untagged lines).
    list       List notes, optionally filtered by --tag or --do (due today).
    show       Print a note with its todos.
    done       Mark a todo item complete.
    rm         Delete a note.
    tags       Print a tally of tagged todo items.
"""

from __future__ import annotations

import argparse
import os
import sys
from datetime import date, datetime
from pathlib import Path


# ---------------------------------------------------------------------------
# Storage model
#
#   ROOT/
#     index            -- one header line per note: slug\t<status>\t<due>  (optional)
#     <slug>/
#       meta.json      -- {"title": ..., "due": "YYYY-MM-DD" | null, "created": iso}
#       todos.txt      -- lines:  [ ] item   |  [x] item   |  [!] item
#
# We keep a small index for cheap `list`/`tags` reads, and the per-note files as
# the source of truth. If the index is missing or stale, operations rebuild it.
# ---------------------------------------------------------------------------

ROOT_ENV = "PNOTES_DIR"

# Tag glyphs (deliberately ASCII-safe so they work in any terminal/copy-paste)
OPEN = "[ ]"     # todo, not started
DONE = "[x]"     # completed
IMPORTANT = "[!]"  # flagged / high priority


def root_dir() -> Path:
    """Resolve the notes root directory (env override or ~/.pnotes)."""
    override = os.environ.get(ROOT_ENV)
    if override:
        p = Path(override)
    else:
        p = Path.home() / ".pnotes"
    p.mkdir(parents=True, exist_ok=True)
    return p


def _slugify(text: str) -> str:
    """Lowercase, strip to ASCII word chars, hyphenate spaces."""
    out = []
    for ch in text.lower():
        if ch.isascii() and ch.isalnum():
            out.append(ch)
        elif ch in " _-":
            out.append("-")
    slug = "".join(out).strip("-")
    # collapse repeated dashes
    prev = None
    collapsed = []
    for ch in slug:
        if ch == "-" and prev == "-":
            continue
        collapsed.append(ch)
        prev = ch
    return "".join(collapsed) or "note"


# ---------------------------------------------------------------------------
# Note object
# ---------------------------------------------------------------------------

class Note:
    def __init__(self, slug: str, data: dict, todos: list[tuple[str, str]]):
        self.slug = slug
        self.data = data            # {title, due, created}
        self.todos = todos          # list of (glyph, text)

    @property
    def title(self) -> str:
        return self.data.get("title", self.slug)

    @property
    def due(self) -> date | None:
        d = self.data.get("due")
        if not d:
            return None
        try:
            return date.fromisoformat(d)
        except ValueError:
            return None

    @property
    def is_overdue(self) -> bool:
        due = self.due
        return bool(due and due < date.today())

    def open_count(self) -> int:
        return sum(1 for g, _ in self.todos if g in (OPEN, IMPORTANT))

    def done_count(self) -> int:
        return sum(1 for g, _ in self.todos if g == DONE)


def note_dir(root: Path, slug: str) -> Path:
    return root / slug


def load_note(root: Path, slug: str) -> Note | None:
    d = note_dir(root, slug)
    meta = d / "meta.json"
    if not meta.exists():
        return None
    import json
    try:
        data = json.loads(meta.read_text())
    except (OSError, ValueError):
        return None
    todos = _read_todos(d / "todos.txt")
    return Note(slug, data, todos)


def _read_todos(path: Path) -> list[tuple[str, str]]:
    if not path.exists():
        return []
    todos = []
    for line in path.read_text().splitlines():
        for glyph in (OPEN, DONE, IMPORTANT):
            if line.startswith(glyph + " "):
                todos.append((glyph, line[len(glyph) + 1:]))
                break
    return todos


def _write_index(root: Path, notes: list[Note]) -> None:
    lines = []
    for n in sorted(notes, key=lambda n: n.title.lower()):
        due = n.data.get("due") or "-"
        lines.append(f"{n.slug}\t{due}\t{n.title}")
    (root / "index").write_text("\n".join(lines) + "\n")


def _load_all(root: Path) -> list[Note]:
    notes = []
    for d in root.iterdir():
        if not d.is_dir():
            continue
        n = load_note(root, d.name)
        if n is not None:
            notes.append(n)
    return notes


# ---------------------------------------------------------------------------
# Errors
# ---------------------------------------------------------------------------

class PnotesError(Exception):
    pass


# ---------------------------------------------------------------------------
# Commands
# ---------------------------------------------------------------------------

def cmd_add(root: Path, args) -> int:
    import json

    title = args.title
    lines: list[str] = list(lines_from_args(args)) if args.untagged else []

    if not title and not args.interactive:
        raise PnotesError("a note needs a title (use -t TITLE or -i for interactive)")
    if not title:
        title = input("Title: ").strip()
    if not title:
        raise PnotesError("a note needs a title")
    if args.interactive and not lines:
        print("Add todo items (one per line, Enter on empty line when done), or . to skip todo section:")
        while True:
            line = input("  > ").strip()
            if line == "":
                break
            lines.append(line)

    slug = _slugify(title)
    while note_dir(root, slug).exists():
        # avoid clobbering an existing note with the same slug
        slug = _slugify(f"{title} {hash(slug) & 0xffff:04x}")

    due = args.due
    if due is not None and not _valid_date(due):
        raise PnotesError(f"invalid due date: {due!r} (expected YYYY-MM-DD)")

    d = note_dir(root, slug)
    d.mkdir(parents=True, exist_ok=True)
    (d / "meta.json").write_text(json.dumps({
        "title": title,
        "due": due,
        "created": datetime.now().isoformat(timespec="seconds"),
    }, indent=2) + "\n")
    if lines:
        body = "\n".join(f"{OPEN} {ln}" for ln in lines)
        (d / "todos.txt").write_text(body + "\n")

    # rebuild index
    notes = _load_all(root)
    _write_sortable(root, notes)

    print(f"added: {slug}  ({title})")
    if due:
        print(f"  due: {due}")
    return 0


def _write_sortable(root: Path, notes: list[Note]) -> None:
    _write_index(root, notes)


def lines_from_args(args) -> list[str]:
    return [a for a in args.untagged if a.strip()]


def _valid_date(s: str) -> bool:
    try:
        date.fromisoformat(s)
        return True
    except ValueError:
        return False


def cmd_list(root: Path, args) -> int:
    notes = _load_all(root)
    if not notes:
        print("no notes yet — add one with `pnotes add`")
        return 0

    today = date.today()
    tag = args.tag
    only_due = args.do

    rows = []
    for n in notes:
        if tag and tag not in _all_tags(n):
            continue
        if only_due and n.due != today:
            continue
        rows.append(n)

    # sort: overdue first, then by due date (none last), then by title
    def sort_key(n: Note):
        due = n.due
        if due is None:
            return (2, date.max, n.title.lower())
        if due < today:
            return (0, due, n.title.lower())
        return (1, due, n.title.lower())

    rows.sort(key=sort_key)

    for n in rows:
        marker = "  [!overdue]" if n.is_overdue else ""
        due = (f"due {n.due.isoformat()}" if n.due else "").ljust(16)
        counts = f"[{n.done_count()}/{n.done_count() + n.open_count()}]"
        title = n.title
        if len(title) > 50:
            title = title[:49] + "…"
        print(f"{n.slug:<32} {due} {counts:<7} {title}{marker}")

    if args.tags:
        print("\n-- tags --")
        for n in notes:
            tg = _all_tags(n)
            if tg:
                print(f"{' '.join('#' + t for t in sorted(tg))}  ({n.slug})")
    return 0


def cmd_show(root: Path, args) -> int:
    n = load_note(root, args.slug)
    if n is None:
        raise PnotesError(f"no such note: {args.slug}")
    due = f"  due {n.due.isoformat()}" if n.due else ""
    over = "  [OVERDUE]" if n.is_overdue else ""
    print(f"# {n.title}  ({n.slug}){due}{over}\n")
    if not n.todos:
        print("(no todo items)")
        return 0
    for i, (glyph, text) in enumerate(n.todos, 1):
        state = "done" if glyph == DONE else ("important" if glyph == IMPORTANT else "open")
        print(f"{i:>2}. {glyph} {text}")

    print(f"\n{n.done_count()} done / {n.open_count()} open")
    return 0


def cmd_done(root: Path, args) -> int:
    n = load_note(root, args.slug)
    if n is None:
        raise PnotesError(f"no such note: {args.slug}")
    if not (1 <= args.item <= len(n.todos)):
        raise PnotesError(f"item {args.item} out of range (note has {len(n.todos)} items)")

    glyph, text = n.todos[args.item - 1]
    if glyph == DONE:
        print(f"item {args.item} already done: {text}")
        return 0
    n.todos[args.item - 1] = (DONE, text)
    _save_todos(root, n)
    print(f"done: {text}")
    return 0


def _save_todos(root: Path, n: Note) -> None:
    lines = [f"{g} {t}" for g, t in n.todos]
    (note_dir(root, n.slug) / "todos.txt").write_text("\n".join(lines) + "\n")


def cmd_rm(root: Path, args) -> int:
    d = note_dir(root, args.slug)
    if not d.exists():
        raise PnotesError(f"no such note: {args.slug}")
    import shutil
    shutil.rmtree(d)
    _write_index(root, _load_all(root))
    print(f"removed: {args.slug}")
    return 0


def _all_tags(n: Note) -> set[str]:
    tags = set()
    for _, text in n.todos:
        for word in text.split():
            if word.startswith("#") and len(word) > 1:
                tags.add(word[1:].rstrip(".,!;:"))
    return tags


def cmd_tags(root: Path, args) -> int:
    from collections import Counter
    counter: Counter[str] = Counter()
    for n in _load_all(root):
        for g, text in n.todos:
            if g == DONE:
                continue
            for word in text.split():
                if word.startswith("#") and len(word) > 1:
                    counter[word[1:].rstrip(".,!;:")] += 1
    if not counter:
        print("no open tagged items")
        return 0
    width = max(len(t) for t in counter)
    for tag, count in counter.most_common():
        print(f"{tag:<{width}}  {'#' * count} {count}")
    return 0


def cmd_stats(root: Path, args) -> int:
    notes = _load_all(root)
    total_open = sum(n.open_count() for n in notes)
    total_done = sum(n.done_count() for n in notes)
    overdue = sum(1 for n in notes if n.is_overdue)
    print(f"notes:     {len(notes)}")
    print(f"todos:     {total_done + total_open} total  ({total_done} done, {total_open} open)")
    print(f"overdue:   {overdue}")
    return 0


# ---------------------------------------------------------------------------
# Cursor handling for the list shortcut (kept simple: just run `list`)
# ---------------------------------------------------------------------------

def cmd_default(root: Path, args) -> int:
    return cmd_list(root, args)


# ---------------------------------------------------------------------------
# arg parsing
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="pnotes",
        description="Tiny dependency-free notes & todo manager.",
    )
    p.add_argument("--dir", help=f"overrides notes root (env {ROOT_ENV})", default=None)
    sub = p.add_subparsers(dest="command")

    a = sub.add_parser("add", help="create a note")
    a.add_argument("--title", "-t", default=None)
    a.add_argument("--due", "-d", default=None, metavar="YYYY-MM-DD")
    a.add_argument("--interactive", "-i", action="store_true", help="prompt for title/items")
    a.add_argument("untagged", nargs="*", help="untagged lines become open todo items")
    a.set_defaults(func=cmd_add)

    l = sub.add_parser("list", aliases=["ls"], help="list notes")
    l.add_argument("--tag", default=None)
    l.add_argument("--do", action="store_true", help="only notes due today")
    l.add_argument("--tags", action="store_true", help="also show tags per note")
    l.set_defaults(func=cmd_list)

    s = sub.add_parser("show", help="show a note")
    s.add_argument("slug")
    s.set_defaults(func=cmd_show)

    d = sub.add_parser("done", help="mark a todo item complete")
    d.add_argument("slug")
    d.add_argument("item", type=int)
    d.set_defaults(func=cmd_done)

    r = sub.add_parser("rm", help="delete a note")
    r.add_argument("slug")
    r.set_defaults(func=cmd_rm)

    t = sub.add_parser("tags", help="tally open tagged items")
    t.set_defaults(func=cmd_tags)

    st = sub.add_parser("stats", help="quick totals")
    st.set_defaults(func=cmd_stats)

    return p


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    root = Path(args.dir) if getattr(args, "dir", None) else root_dir()

    try:
        if getattr(args, "func", None) is None:
            # no subcommand: default to list
            return cmd_list(root, args)
        return args.func(root, args)
    except PnotesError as e:
        print(f"error: {e}", file=sys.stderr)
        return 1
    except KeyboardInterrupt:
        print("\n(aborted)", file=sys.stderr)
        return 130


if __name__ == "__main__":
    sys.exit(main())
