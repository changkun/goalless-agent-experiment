import random

from peak.affirmations import AFFIRMATIONS, random_affirmation
from peak.cli import build_parser, main


def test_random_affirmation_is_valid():
    rng = random.Random(0)
    for _ in range(100):
        assert random_affirmation(rng) in AFFIRMATIONS


def test_parser_defaults():
    args = build_parser().parse_args([])
    assert args.name == "champion"
    assert args.streak == 0
    assert args.quiet is False


def test_main_returns_zero(capsys):
    assert main(["-n", "Sam", "-s", "7"]) == 0
    out = capsys.readouterr().out
    assert "Sam" in out
    assert "7-day streak" in out


def test_quiet_prints_no_art(capsys):
    main(["-q"])
    out = capsys.readouterr().out
    assert "PEAK" not in out
