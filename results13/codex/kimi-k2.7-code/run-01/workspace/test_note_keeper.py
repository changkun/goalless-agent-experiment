"""Tests for note_keeper.py (uses only stdlib)."""

import json
from pathlib import Path

import note_keeper


def test_load_save_notes(tmp_path: Path) -> None:
    notes_file = tmp_path / "notes.json"
    note_keeper.save_notes(notes_file, [{"id": 1, "text": "hello"}])
    notes = note_keeper.load_notes(notes_file)
    assert notes == [{"id": 1, "text": "hello"}]


def test_load_missing_file(tmp_path: Path) -> None:
    assert note_keeper.load_notes(tmp_path / "missing.json") == []


def test_load_corrupt_file(tmp_path: Path) -> None:
    notes_file = tmp_path / "notes.json"
    notes_file.write_text("not json")
    assert note_keeper.load_notes(notes_file) == []


def test_add_and_list(tmp_path: Path) -> None:
    notes_file = tmp_path / "notes.json"
    assert note_keeper.main(["--file", str(notes_file), "add", "Buy milk"]) == 0
    assert note_keeper.main(["--file", str(notes_file), "list"]) == 0
    notes = note_keeper.load_notes(notes_file)
    assert len(notes) == 1
    assert notes[0]["text"] == "Buy milk"


def test_search(tmp_path: Path) -> None:
    notes_file = tmp_path / "notes.json"
    note_keeper.main(["--file", str(notes_file), "add", "Buy milk"])
    note_keeper.main(["--file", str(notes_file), "add", "Walk dog"])
    assert note_keeper.main(["--file", str(notes_file), "search", "milk"]) == 0


def test_delete(tmp_path: Path) -> None:
    notes_file = tmp_path / "notes.json"
    note_keeper.main(["--file", str(notes_file), "add", "Buy milk"])
    assert note_keeper.main(["--file", str(notes_file), "delete", "1"]) == 0
    assert note_keeper.load_notes(notes_file) == []


def test_delete_missing(tmp_path: Path) -> None:
    notes_file = tmp_path / "notes.json"
    assert note_keeper.main(["--file", str(notes_file), "delete", "99"]) == 1
