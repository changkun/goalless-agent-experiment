"""Tokenizer, parser, and printer for tinylisp source text."""

from __future__ import annotations

import re
from typing import Any, List, Optional, Tuple

from .types import Keyword, LispError, Procedure, Symbol

TOKEN_RE = re.compile(
    r"""
    (?P<ws>[\s,]+)
  | (?P<comment>;[^\n]*)
  | (?P<string>"(?:\\.|[^"\\])*"?)
  | (?P<quote>['`]|~@|~)
  | (?P<paren>[()\[\]])
  | (?P<atom>[^\s,()\[\]"';`~]+)
    """,
    re.VERBOSE,
)

ESCAPES = {"n": "\n", "t": "\t", "r": "\r", '"': '"', "\\": "\\"}

QUOTE_FORMS = {
    "'": "quote",
    "`": "quasiquote",
    "~": "unquote",
    "~@": "unquote-splicing",
}


def tokenize(source: str) -> List[Tuple[str, str]]:
    tokens: List[Tuple[str, str]] = []
    position = 0
    while position < len(source):
        match = TOKEN_RE.match(source, position)
        if match is None:
            raise LispError(f"unexpected character {source[position]!r}")
        position = match.end()
        kind = match.lastgroup
        if kind in ("ws", "comment"):
            continue
        assert kind is not None
        tokens.append((kind, match.group()))
    return tokens


def parse_atom(text: str) -> Any:
    if text == "nil":
        return None
    if text == "true":
        return True
    if text == "false":
        return False
    try:
        return int(text)
    except ValueError:
        pass
    try:
        return float(text)
    except ValueError:
        pass
    if text.startswith(":") and len(text) > 1:
        return Keyword(text)
    return Symbol(text)


def unescape(literal: str) -> str:
    if len(literal) < 2 or not literal.endswith('"'):
        raise LispError("unterminated string literal")
    body = literal[1:-1]
    out: List[str] = []
    index = 0
    while index < len(body):
        char = body[index]
        if char == "\\":
            index += 1
            if index >= len(body):
                raise LispError("dangling escape in string literal")
            out.append(ESCAPES.get(body[index], body[index]))
        else:
            out.append(char)
        index += 1
    return "".join(out)


class Reader:
    """Consumes a token stream into tinylisp data."""

    def __init__(self, tokens: List[Tuple[str, str]]) -> None:
        self.tokens = tokens
        self.index = 0

    def at_end(self) -> bool:
        return self.index >= len(self.tokens)

    def peek(self) -> Optional[Tuple[str, str]]:
        return None if self.at_end() else self.tokens[self.index]

    def next(self) -> Tuple[str, str]:
        if self.at_end():
            raise LispError("unexpected end of input")
        token = self.tokens[self.index]
        self.index += 1
        return token

    def read_form(self) -> Any:
        kind, text = self.next()
        if kind == "quote":
            return [Symbol(QUOTE_FORMS[text]), self.read_form()]
        if kind == "string":
            return unescape(text)
        if kind == "paren":
            if text in ")]":
                raise LispError(f"unexpected {text!r}")
            closer = ")" if text == "(" else "]"
            return self.read_sequence(closer)
        return parse_atom(text)

    def read_sequence(self, closer: str) -> List[Any]:
        items: List[Any] = []
        while True:
            token = self.peek()
            if token is None:
                raise LispError(f"expected {closer!r} before end of input")
            if token[0] == "paren" and token[1] == closer:
                self.index += 1
                return items
            if token[0] == "paren" and token[1] in ")]":
                raise LispError(f"expected {closer!r}, found {token[1]!r}")
            items.append(self.read_form())


def read_all(source: str) -> List[Any]:
    """Parse every top-level form in ``source``."""
    reader = Reader(tokenize(source))
    forms: List[Any] = []
    while not reader.at_end():
        forms.append(reader.read_form())
    return forms


def read_one(source: str) -> Any:
    forms = read_all(source)
    if len(forms) != 1:
        raise LispError(f"expected exactly one form, got {len(forms)}")
    return forms[0]


def escape(text: str) -> str:
    out = ['"']
    for char in text:
        if char in '"\\':
            out.append("\\" + char)
        elif char == "\n":
            out.append("\\n")
        elif char == "\t":
            out.append("\\t")
        else:
            out.append(char)
    out.append('"')
    return "".join(out)


def to_string(value: Any, readable: bool = True) -> str:
    """Render ``value`` the way the REPL prints it."""
    if value is None:
        return "nil"
    if value is True:
        return "true"
    if value is False:
        return "false"
    if isinstance(value, (Symbol, Keyword)):
        return str(value)
    if isinstance(value, str):
        return escape(value) if readable else value
    if isinstance(value, list):
        return "(" + " ".join(to_string(item, readable) for item in value) + ")"
    if isinstance(value, dict):
        pairs = " ".join(
            f"{to_string(key, readable)} {to_string(val, readable)}"
            for key, val in value.items()
        )
        return "{" + pairs + "}"
    if isinstance(value, float) and value.is_integer():
        return f"{value:.1f}"
    if isinstance(value, Procedure):
        return repr(value)
    if callable(value):
        name = getattr(value, "lisp_name", getattr(value, "__name__", "fn"))
        return f"#<builtin {name}>"
    return str(value)
