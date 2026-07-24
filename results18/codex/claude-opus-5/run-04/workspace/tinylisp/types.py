"""Core data types for the tinylisp language."""

from __future__ import annotations

from typing import Any, Dict, Iterator, List, Optional


class Symbol(str):
    """An interned identifier. Distinct from a Lisp string."""

    __slots__ = ()

    def __repr__(self) -> str:  # pragma: no cover - debugging aid
        return f"Symbol({str.__repr__(self)})"


class Keyword(str):
    """A self-evaluating name such as ``:name``."""

    __slots__ = ()


class LispError(Exception):
    """Raised for any error surfaced to the user of the interpreter."""


class Environment:
    """A lexical scope chained to an optional parent scope."""

    __slots__ = ("vars", "parent")

    def __init__(
        self,
        vars: Optional[Dict[str, Any]] = None,
        parent: "Optional[Environment]" = None,
    ) -> None:
        self.vars: Dict[str, Any] = dict(vars or {})
        self.parent = parent

    def lookup(self, name: str) -> Any:
        scope: Optional[Environment] = self
        while scope is not None:
            if name in scope.vars:
                return scope.vars[name]
            scope = scope.parent
        raise LispError(f"unbound symbol: {name}")

    def define(self, name: str, value: Any) -> Any:
        self.vars[name] = value
        return value

    def set(self, name: str, value: Any) -> Any:
        scope: Optional[Environment] = self
        while scope is not None:
            if name in scope.vars:
                scope.vars[name] = value
                return value
            scope = scope.parent
        raise LispError(f"cannot set! unbound symbol: {name}")


class Procedure:
    """A user-defined function or macro closing over its defining scope."""

    __slots__ = ("params", "rest", "body", "env", "name", "is_macro")

    def __init__(
        self,
        params: List[Symbol],
        rest: Optional[Symbol],
        body: List[Any],
        env: Environment,
        name: str = "lambda",
        is_macro: bool = False,
    ) -> None:
        self.params = params
        self.rest = rest
        self.body = body
        self.env = env
        self.name = name
        self.is_macro = is_macro

    def bind(self, args: List[Any]) -> Environment:
        required = len(self.params)
        if len(args) < required or (self.rest is None and len(args) > required):
            expected = f"{required}{'+' if self.rest else ''}"
            raise LispError(
                f"{self.name} expects {expected} argument(s), got {len(args)}"
            )
        scope = Environment(parent=self.env)
        for param, value in zip(self.params, args):
            scope.vars[param] = value
        if self.rest is not None:
            scope.vars[self.rest] = list(args[required:])
        return scope

    def __repr__(self) -> str:
        kind = "macro" if self.is_macro else "procedure"
        return f"#<{kind} {self.name}>"


class TailCall:
    """Internal marker used to implement tail-call elimination."""

    __slots__ = ("expr", "env")

    def __init__(self, expr: Any, env: Environment) -> None:
        self.expr = expr
        self.env = env


def iterate(value: Any) -> Iterator[Any]:
    if isinstance(value, (list, tuple)):
        return iter(value)
    if isinstance(value, str):
        return iter(value)
    raise LispError(f"not iterable: {value!r}")
