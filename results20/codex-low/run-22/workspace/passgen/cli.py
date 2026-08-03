"""Command-line interface for passgen."""

from __future__ import annotations

import argparse
import getpass
import json
import os
import sys

from . import __version__
from .core import (
    PasswordConfig,
    generate_passphrase,
    generate_password,
    generate_token,
    pool_size,
)
from .vault import Vault


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="passgen",
        description="Dependency-free password, token and passphrase generator with an encrypted vault.",
    )
    parser.add_argument("--version", action="version", version=__version__)
    sub = parser.add_subparsers(dest="command")

    pw = sub.add_parser("generate", help="generate a random password")
    _add_length(pw)
    _add_flags(pw)

    tok = sub.add_parser("token", help="generate a random token / API key")
    tok.add_argument("-l", "--length", type=int, default=32, help="token length (default 32)")
    tok.add_argument("-a", "--alphabet", default=None, help="custom alphabet")

    phrase = sub.add_parser("passphrase", help="generate a Diceware-style passphrase")
    phrase.add_argument("-w", "--words", type=int, default=6, help="number of words (default 6)")
    phrase.add_argument("-s", "--separator", default="-", help="word separator (default '-')")
    phrase.add_argument("-c", "--capitalize", action="store_true", help="capitalize words")
    phrase.add_argument("--wordlist", default=None, help="path to a custom wordlist")

    info = sub.add_parser("info", help="show entropy for given settings")
    _add_length(info)
    _add_flags(info, require_length=True)

    vz = sub.add_parser("vault", help="manage an encrypted password store")
    vz.add_argument("action", choices=["init", "add", "get", "list", "delete", "setpass"])
    vz.add_argument("name", nargs="?", help="entry name")
    vz.add_argument("value", nargs="*", help="key=value fields (for add/setpass)")
    vz.add_argument("-f", "--file", default=os.environ.get("PASSGEN_VAULT", "vault.json"),
                    help="vault file path (default: vault.json, or $PASSGEN_VAULT)")

    return parser


def _add_length(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("-l", "--length", type=int, default=16, help="length (default 16)")


def _add_flags(parser: argparse.ArgumentParser, require_length: bool = False) -> None:
    parser.add_argument("--no-lower", action="store_true", help="exclude lowercase")
    parser.add_argument("--no-upper", action="store_true", help="exclude uppercase")
    parser.add_argument("--no-digits", action="store_true", help="exclude digits")
    parser.add_argument("--no-symbols", action="store_true", help="exclude symbols")
    parser.add_argument("--no-ambiguous", action="store_true", help="exclude ambiguous chars (Il1O0)")


def _config_from(parser: argparse.ArgumentParser, args: argparse.Namespace) -> PasswordConfig:
    return PasswordConfig(
        length=args.length,
        lowercase=not args.no_lower,
        uppercase=not args.no_upper,
        digits=not args.no_digits,
        symbols=not args.no_symbols,
        exclude_ambiguous=args.no_ambiguous,
    )


def _prompt_master(confirm: bool = False) -> str:
    pw = getpass.getpass("Master password: ")
    if confirm:
        again = getpass.getpass("Confirm password: ")
        if pw != again:
            sys.exit("Passwords do not match")
    return pw


def _cmd_generate(args: argparse.Namespace) -> int:
    print(generate_password(_config_from(argparse.Namespace(), args)))
    return 0


def _cmd_token(args: argparse.Namespace) -> int:
    print(generate_token(length=args.length, alphabet=args.alphabet) if args.alphabet
          else generate_token(length=args.length))
    return 0


def _cmd_passphrase(args: argparse.Namespace) -> int:
    wordlist = None
    if args.wordlist:
        with open(args.wordlist, "r", encoding="utf-8") as handle:
            wordlist = handle.read().split()
    print(generate_passphrase(words=args.words, separator=args.separator,
                              capitalize=args.capitalize, wordlist=wordlist))
    return 0


def _cmd_info(args: argparse.Namespace) -> int:
    import math
    config = _config_from(argparse.Namespace(), args)
    ps = pool_size(config)
    bits = config.length * math.log2(ps)
    print(f"pool size : {ps} characters")
    print(f"length    : {config.length}")
    print(f"entropy   : {bits:.1f} bits")
    return 0


def _cmd_vault(args: argparse.Namespace) -> int:
    from .core import generate_password

    if args.action == "init":
        if os.path.exists(args.file):
            sys.exit(f"vault already exists: {args.file}")
        pw = _prompt_master(confirm=True)
        vault = Vault.open(args.file, pw)
        vault.save()
        print(f"created vault: {args.file}")
        return 0

    pw = _prompt_master()
    vault = Vault.open(args.file, pw)

    if args.action == "add":
        if not args.name or not args.value:
            sys.exit("usage: passgen vault add <name> key=value [key=value ...]")
        fields = dict(pair.split("=", 1) for pair in args.value)
        if "password" not in fields:
            fields["password"] = generate_password()
        vault.set(args.name, **fields)
        vault.save()
        print(f"saved {args.name}")
        return 0

    if args.action == "get":
        entry = vault.get(args.name or "")
        if entry is None:
            sys.exit(f"no such entry: {args.name}")
        for key, value in entry.items():
            print(f"{key}: {value}")
        return 0

    if args.action == "list":
        for name in vault.names():
            print(name)
        return 0

    if args.action == "delete":
        if vault.delete(args.name or ""):
            vault.save()
            print(f"deleted {args.name}")
            return 0
        sys.exit(f"no such entry: {args.name}")

    if args.action == "setpass":
        new_pw = _prompt_master(confirm=True)
        vault.change_password(new_pw)
        vault.save()
        print("password updated")
        return 0

    return 2


def main(argv: list[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)
    if not args.command:
        parser.print_help()
        return 2

    commands = {
        "generate": _cmd_generate,
        "token": _cmd_token,
        "passphrase": _cmd_passphrase,
        "info": _cmd_info,
        "vault": _cmd_vault,
    }
    return commands[args.command](args)


if __name__ == "__main__":
    sys.exit(main())
