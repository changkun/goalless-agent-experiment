"""Unit tests for apod_cli — all offline."""
from __future__ import annotations

import sys
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from apod.client import ApodData, _parse, ApodError
from apod.render import (
    _strip_html,
    render_html,
    render_markdown,
    render_terminal,
)


SAMPLE = {
    "date": "2024-08-12",
    "title": "Milky Way over the Alps",
    "explanation": "<p>Stars shine over <b>snowy</b> peaks.</p>",
    "media_type": "image",
    "url": "https://apod.nasa.gov/apod/image/2408/alps_960.jpg",
    "hdurl": "https://apod.nasa.gov/apod/image/2408/alps_hd.jpg",
    "copyright": "Jean-Marie Malherbe",
    "service_version": "v1",
}

VIDEO = {
    "date": "2023-04-01",
    "title": "A Cosmic Video",
    "explanation": "Just some moving pixels.",
    "media_type": "video",
    "url": "https://www.youtube.com/embed/abc",
    "service_version": "v1",
}


def make_data(raw):
    return _parse(raw)


def test_parse_full_payload():
    item = make_data(SAMPLE)
    assert item.date == date(2024, 8, 12)
    assert item.title == "Milky Way over the Alps"
    assert item.is_image
    assert item.hdurl and item.hdurl.startswith("https://")
    assert item.copyright == "Jean-Marie Malherbe"


def test_parse_minimal_payload():
    minimal = {
        "date": "2020-01-01",
        "title": "Hello",
        "explanation": "World",
        "media_type": "image",
        "url": "https://example.com/x.jpg",
    }
    item = make_data(minimal)
    assert item.hdurl is None
    assert item.copyright is None
    assert item.is_image


def test_parse_missing_field_raises():
    bad = {k: v for k, v in SAMPLE.items() if k != "title"}
    try:
        make_data(bad)
    except ApodError as exc:
        assert "title" in str(exc)
    else:
        raise AssertionError("expected ApodError for missing title")


def test_video_item():
    item = make_data(VIDEO)
    assert item.is_video
    assert not item.is_image


def test_terminal_render_contains_title_and_date():
    item = make_data(SAMPLE)
    text = render_terminal([item], width=80)
    assert "Milky Way over the Alps" in text
    assert "Monday, August 12, 2024" in text
    assert "IMAGE" in text
    assert "<p>" not in text
    assert "<b>" not in text
    assert "Jean-Marie Malherbe" in text


def test_markdown_render():
    item = make_data(SAMPLE)
    md = render_markdown([item])
    assert md.startswith("# \u2728 Milky Way over the Alps") or md.startswith("# \u2726 Milky Way over the Alps")
    assert "![Milky Way over the Alps](https://apod.nasa.gov/apod/image/2408/alps_hd.jpg)" in md
    assert "[Open on NASA]" in md
    assert "*Jean-Marie Malherbe*" in md


def test_markdown_video_skips_image():
    item = make_data(VIDEO)
    md = render_markdown([item])
    assert "![" not in md
    assert "video" in md


def test_html_render_escapes_content():
    item = make_data(SAMPLE)
    html = render_html([item], title="My APOD")
    assert "<title>My APOD</title>" in html
    assert "&lt;p&gt;" in html
    assert "<img" in html
    assert "https://apod.nasa.gov/apod/image/2408/alps_hd.jpg" in html


def test_strip_html_basic():
    assert _strip_html("<a href='x'>link</a>") == "link"
    assert _strip_html("plain <b>bold</b> text") == "plain bold text"


def test_terminal_render_empty():
    assert "No APOD entries" in render_terminal([])


if __name__ == "__main__":  # pragma: no cover
    import pytest
    raise SystemExit(pytest.main([__file__, "-q"]))
