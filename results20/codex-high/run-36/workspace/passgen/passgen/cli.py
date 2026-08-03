"""Command-line interface for passgen."""

from __future__ import annotations

import argparse

from .core import StrengthError, analyze_strength, generate_password

GRADES = {
    "very weak": "red",
    "weak": "red",
    "moderate": "yellow",
    "strong": "green",
    "very strong": "green",
}

# Minimal ANSI coloring, disabled when not a TTY.
USE_COLOR = False


def _color(text: str, color: str) -> str:
    if not USE_COLOR:
        return text
    code = {"red": 31, "yellow": 33, "green": 32, "cyan": 36}.get(color, 0)
    return f"\033[{code}m{text}\033[0m"


def _print_strength(password: str) -> None:
    info = analyze_strength(password)
    color = GRADES[info["grade"]]

    print()
    print(f"Length:        {info['length']}")
    print(f"Entropy:       {info['entropy_bits']} bits")
    print(f"Character set: {'/'.join(c for c, used in info['charset_used'].items() if used)}")
    print(
        f"Grade:         {_color(info['grade'].upper(), color)}"
        f"  (score {info['score']}/4)"
    )
    print(
        f"Suggestion:    use a {_color('password manager', 'cyan')} "
        "and enable multi-factor auth"
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="passgen",
        description="Generate secure passwords and analyze their strength.",
    )
    parser.add_argument(
        "target",
        nargs="?",
        help="password to analyze (only ASCII-printable characters supported in output)",
    )
    parser.add_argument("-n", "--length", type=int, default=16, help="password length (default: 16)")
    parser.add_argument("--no-lowercase", action="store_true", help="exclude lowercase letters")
    parser.add_argument("--no-uppercase", action="store_true", help="exclude uppercase letters")
    parser.add_argument("--no-digits", action="store_true", help="exclude digits")
    parser.add_argument("--no-symbols", action="store_true", help="exclude symbols")
    parser.add_argument("--no-ambiguous", action="store_true", help="exclude confusing characters (Il1O0o)")
    parser.add_argument("--analyze", action="store_true", help="read password from stdin and analyze it")
    parser.add_argument("--count", type=int, default=1, help="number of passwords to generate (default: 1)")
    parser.add_argument("--no-color", action="store_true", help="disable colored output")
    return parser


def main(argv: list[str] | None = None) -> int:
    global USE_COLOR
    args = build_parser().parse_args(argv)

    try:
        import sys

        USE_COLOR = not args.no_color and sys.stdout.isatty()
    except Exception:
        USE_COLOR = False

    try:
        if args.target or args.analyze:
            import getpass
            import sys

            target = args.target
            if target is None:
                target = getpass.getpass("Password to analyze: ")
            _print_strength(target)
            return 0

        for i in range(args.count):
            password = generate_password(
                length=args.length,
                lowercase=not args.no_lowercase,
                uppercase=not args.no_uppercase,
                digits=not args.no_digits,
                symbols=not args.no_symbols,
                exclude_ambiguous=args.no_ambiguous,
            )
            print(password)
        return 0
    except (StrengthError, ValueError) as e:
        import sys

        print(f"error: {e}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
