import os
import tempfile

import pytest

from pocket import core


@pytest.fixture()
def journal():
    with tempfile.TemporaryDirectory() as tmp:
        path = os.path.join(tmp, "journal.md")
        yield path


def test_add_and_read_note(journal):
    core.add(journal, "hello world")
    items = core.read(journal)
    assert len(items) == 1
    assert items[0].text == "hello world"
    assert items[0].task is False


def test_add_task_and_done(journal):
    core.add(journal, "do the thing", task=True)
    core.add(journal, "already done", task=True, done=True)
    items = core.list_items(journal, kind="tasks")
    assert [i.done for i in items] == [True, False]


def test_list_filters(journal):
    core.add(journal, "a note")
    core.add(journal, "a task", task=True)
    assert core.list_items(journal, kind="notes")[0].text == "a note"
    assert core.list_items(journal, kind="tasks")[0].text == "a task"
    assert len(core.list_items(journal, kind="all")) == 2


def test_set_done(journal):
    core.add(journal, "task a", task=True)
    core.add(journal, "task b", task=True)
    # list is newest-first, so index 0 = "task b"
    core.set_done(journal, 0, True)
    items = core.list_items(journal, kind="tasks")
    assert items[0].done is True   # task b
    assert items[1].done is False  # task a


def test_set_done_out_of_range(journal):
    assert core.set_done(journal, 5, True) is None


def test_remove(journal):
    core.add(journal, "keep me")
    core.add(journal, "drop me")
    core.remove(journal, 0)  # newest-first -> "drop me"
    items = core.read(journal)
    assert [i.text for i in items] == ["keep me"]


def test_read_missing_file(journal):
    assert core.read(os.path.join(journal, "nope", "x.md")) == []


def test_mutating_existing_file_keeps_sections(journal):
    core.add(journal, "first", task=True)
    core.add(journal, "second", task=True)
    core.set_done(journal, 0, True)
    with open(journal) as fh:
        content = fh.read()
    assert content.count("##") == 1
    assert "[x]" in content
