"""Tests for pnotes. Run with:  python3 -m pytest  (or: python3 test_pnotes.py)"""

import sys
import os
import tempfile
from pathlib import Path
from datetime import date

import pnotes

ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ROOT)


def make_root() -> Path:
    d = tempfile.mkdtemp(prefix="pnotes-test-")
    return Path(d)


def run(root: Path, *argv: str) -> int:
    return pnotes.main(["--dir", str(root), *argv])


def add_note(root, title, *lines, due=None):
    argv = ["add", "--title", title]
    if due:
        argv += ["--due", due]
    argv += list(lines)
    return run(root, *argv)


def test_slugify():
    assert pnotes._slugify("  Hi There  ") == "hi-there"
    assert pnotes._slugify("Café & Tea!!!") == "caf-tea"
    assert pnotes._slugify("---") == "note"
    assert pnotes._slugify("a--b") == "a-b"


def test_add_and_show():
    root = make_root()
    assert add_note(root, "Groceries", "Milk", "Bread #errand", due="2026-12-01") == 0
    n = pnotes.load_note(root, "groceries")
    assert n is not None
    assert n.title == "Groceries"
    assert n.due == date(2026, 12, 1)
    assert n.open_count() == 2
    assert n.done_count() == 0


def test_add_requires_title():
    root = make_root()
    assert run(root, "add", "-t", "") != 0


def test_invalid_due_rejected():
    root = make_root()
    assert run(root, "add", "-t", "x", "--due", "not-a-date") != 0


def test_done_updates_state():
    root = make_root()
    add_note(root, "Tasks", "one", "two")
    n = pnotes.load_note(root, "tasks")
    assert run(root, "done", "tasks", "1") == 0
    n2 = pnotes.load_note(root, "tasks")
    assert n2.done_count() == 1
    assert n2.open_count() == 1
    # item out of range
    assert run(root, "done", "tasks", "99") != 0
    # double-complete
    assert run(root, "done", "tasks", "1") == 0


def test_duplicate_slug_does_not_clobber():
    root = make_root()
    add_note(root, "Same")
    add_note(root, "Same")
    notes = pnotes._load_all(root)
    assert len(notes) == 2


def test_rm():
    root = make_root()
    add_note(root, "Temp")
    assert (root / "temp").exists()
    assert run(root, "rm", "temp") == 0
    assert not (root / "temp").exists()


def test_rm_missing():
    root = make_root()
    assert run(root, "rm", "nope") != 0


def test_tags_tally():
    root = make_root()
    add_note(root, "A", "do the #laundry", "get #coffee")
    add_note(root, "B", "already #coffee")
    run(root, "done", "b", "1")  # mark B's #coffee done -> excluded
    assert run(root, "tags") == 0


def test_list_tag_filter():
    root = make_root()
    add_note(root, "A", "x #work")
    add_note(root, "B", "y #home")
    out = io_capture(root, "list", "--tag", "work")
    assert "a" in out and "b" not in out


def test_index_written():
    root = make_root()
    add_note(root, "Zebra")
    add_note(root, "Apple")
    idx = (root / "index").read_text()
    # sorted alphabetically by title: Apple before Zebra
    assert idx.index("apple") < idx.index("zebra")


import io


def io_capture(root, *argv) -> str:
    import contextlib
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        pnotes.main(["--dir", str(root), *argv])
    return buf.getvalue()


if __name__ == "__main__":
    import traceback
    failures = 0
    for name, fn in sorted(globals().items()):
        if name.startswith("test_") and callable(fn):
            try:
                fn()
                print(f"PASS  {name}")
            except Exception:
                failures += 1
                print(f"FAIL  {name}")
                traceback.print_exc()
    print(f"\n{failures} failure(s)")
    sys.exit(1 if failures else 0)
