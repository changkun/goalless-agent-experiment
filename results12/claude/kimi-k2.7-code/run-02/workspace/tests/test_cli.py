"""Tests for serendipity.cli."""

import pytest

from serendipity.cli import build_parser, main


def test_parser_defaults():
    args = build_parser().parse_args([])
    assert args.category is None
    assert args.file is None
    assert args.list is False


def test_parser_category():
    args = build_parser().parse_args(["--category", "create"])
    assert args.category == "create"


def test_main_list(capsys):
    code = main(["--list"])
    captured = capsys.readouterr()
    assert code == 0
    assert "Find a color" in captured.out


def test_main_category_filter(capsys):
    code = main(["--category", "move"])
    captured = capsys.readouterr()
    assert code == 0
    assert "[Move]" in captured.out


def test_main_no_prompts_for_category(tmp_path):
    empty = tmp_path / "empty.json"
    empty.write_text("[]")
    code = main(["--category", "move", "--file", str(empty)])
    assert code == 1


def test_main_version():
    with pytest.raises(SystemExit) as exc:
        main(["--version"])
    assert exc.value.code == 0
