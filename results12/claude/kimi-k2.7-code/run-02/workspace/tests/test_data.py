"""Tests for serendipity.data."""

from pathlib import Path

import pytest

from serendipity.data import DEFAULT_PROMPTS, Category, load_prompts, pick


def test_default_prompts_non_empty():
    assert len(DEFAULT_PROMPTS) > 0


def test_pick_returns_prompt():
    prompt = pick(DEFAULT_PROMPTS)
    assert prompt is not None
    assert prompt in DEFAULT_PROMPTS


def test_pick_by_category():
    prompt = pick(DEFAULT_PROMPTS, Category.OBSERVE)
    assert prompt is not None
    assert prompt.category == Category.OBSERVE


def test_pick_unknown_category_returns_none():
    assert pick((), Category.WONDER) is None


def test_load_prompts_defaults_when_file_missing(tmp_path: Path):
    assert load_prompts(tmp_path / "nope.json") == DEFAULT_PROMPTS


def test_load_prompts_defaults_on_invalid_json(tmp_path: Path):
    bad = tmp_path / "bad.json"
    bad.write_text("not json")
    assert load_prompts(bad) == DEFAULT_PROMPTS


def test_load_prompts_custom_file(tmp_path: Path):
    custom = tmp_path / "custom.json"
    custom.write_text(
        '[{"category": "wonder", "text": "Test prompt", "why": "Because."}]'
    )
    loaded = load_prompts(custom)
    assert len(loaded) == 1
    assert loaded[0].category == Category.WONDER
    assert loaded[0].text == "Test prompt"
