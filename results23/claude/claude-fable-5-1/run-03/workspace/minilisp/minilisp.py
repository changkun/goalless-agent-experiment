#!/usr/bin/env python3
"""minilisp: a small Scheme-flavoured Lisp interpreter.

Features: integers/floats/strings/booleans, symbols, quote, if, define, set!,
lambda with lexical closures, begin, let, cond, and/or, proper tail calls,
a handful of list/numeric primitives, and a REPL.
"""
from __future__ import annotations

import math
import operator as op
import sys
from dataclasses import dataclass
from typing import Any, Callable


# ---------------------------------------------------------------- data types

class Symbol(str):
    """Interned identifier. Distinct from Python str so strings stay strings."""
    __slots__ = ()

    def __repr__(self) -> str:
        return str(self)


_symtab: dict[str, Symbol] = {}


def sym(name: str) -> Symbol:
    s = _symtab.get(name)
    if s is None:
        s = _symtab[name] = Symbol(name)
    return s


class Nil:
    __slots__ = ()

    def __repr__(self) -> str:
        return "()"

    def __bool__(self) -> bool:
        return True  # only #f is false in Scheme

    def __iter__(self):
        return iter(())


NIL = Nil()


@dataclass(slots=True)
class Pair:
    car: Any
    cdr: Any

    def __iter__(self):
        node: Any = self
        while isinstance(node, Pair):
            yield node.car
            node = node.cdr
        if node is not NIL:
            raise LispError("improper list in iteration")

    def __repr__(self) -> str:
        return to_string(self)


def lst(*items: Any, tail: Any = NIL) -> Any:
    out = tail
    for item in reversed(items):
        out = Pair(item, out)
    return out


class LispError(Exception):
    pass


# ------------------------------------------------------------------- parser

def tokenize(src: str) -> list[str]:
    tokens: list[str] = []
    i, n = 0, len(src)
    while i < n:
        c = src[i]
        if c.isspace():
            i += 1
        elif c == ";":
            while i < n and src[i] != "\n":
                i += 1
        elif c in "()'":
            tokens.append(c)
            i += 1
        elif c == '"':
            j = i + 1
            buf = []
            while j < n and src[j] != '"':
                if src[j] == "\\" and j + 1 < n:
                    j += 1
                    buf.append({"n": "\n", "t": "\t", '"': '"', "\\": "\\"}.get(src[j], src[j]))
                else:
                    buf.append(src[j])
                j += 1
            if j >= n:
                raise LispError("unterminated string literal")
            tokens.append('"' + "".join(buf))  # leading quote marks a string token
            i = j + 1
        else:
            j = i
            while j < n and not src[j].isspace() and src[j] not in "()';\"":
                j += 1
            tokens.append(src[i:j])
            i = j
    return tokens


def atom(tok: str) -> Any:
    if tok[0] == '"':
        return tok[1:]
    if tok == "#t":
        return True
    if tok == "#f":
        return False
    try:
        return int(tok)
    except ValueError:
        pass
    try:
        return float(tok)
    except ValueError:
        pass
    return sym(tok)


def parse_all(src: str) -> list[Any]:
    tokens = tokenize(src)
    pos = 0

    def read() -> Any:
        nonlocal pos
        if pos >= len(tokens):
            raise LispError("unexpected end of input")
        tok = tokens[pos]
        pos += 1
        if tok == "(":
            items = []
            while True:
                if pos >= len(tokens):
                    raise LispError("missing ')'")
                if tokens[pos] == ")":
                    pos += 1
                    return lst(*items)
                if tokens[pos] == ".":
                    if not items:
                        raise LispError("unexpected '.'")
                    pos += 1
                    tail = read()
                    if pos >= len(tokens) or tokens[pos] != ")":
                        raise LispError("expected ')' after dotted tail")
                    pos += 1
                    return lst(*items, tail=tail)
                items.append(read())
        if tok == ")":
            raise LispError("unexpected ')'")
        if tok == "'":
            return lst(sym("quote"), read())
        return atom(tok)

    forms = []
    while pos < len(tokens):
        forms.append(read())
    return forms


def parse(src: str) -> Any:
    forms = parse_all(src)
    if len(forms) != 1:
        raise LispError(f"expected exactly one expression, got {len(forms)}")
    return forms[0]


# ------------------------------------------------------------------ printer

def to_string(x: Any) -> str:
    if x is True:
        return "#t"
    if x is False:
        return "#f"
    if x is NIL:
        return "()"
    if isinstance(x, Symbol):
        return str(x)
    if isinstance(x, str):
        escaped = x.replace("\\", "\\\\").replace('"', '\\"').replace("\n", "\\n")
        return f'"{escaped}"'
    if isinstance(x, Pair):
        parts = []
        node: Any = x
        while isinstance(node, Pair):
            parts.append(to_string(node.car))
            node = node.cdr
        if node is not NIL:
            parts.append(".")
            parts.append(to_string(node))
        return "(" + " ".join(parts) + ")"
    if isinstance(x, Lambda):
        return f"#<lambda {to_string(x.params)}>"
    if callable(x):
        return f"#<primitive {getattr(x, '__name__', '?')}>"
    if isinstance(x, float) and x.is_integer() and abs(x) < 1e16:
        return f"{x:.1f}"
    return repr(x)


# -------------------------------------------------------------- environment

class Env:
    __slots__ = ("vars", "outer")

    def __init__(self, vars: dict[Symbol, Any] | None = None, outer: "Env | None" = None):
        self.vars = vars if vars is not None else {}
        self.outer = outer

    def find(self, name: Symbol) -> "Env":
        env: Env | None = self
        while env is not None:
            if name in env.vars:
                return env
            env = env.outer
        raise LispError(f"unbound symbol: {name}")

    def lookup(self, name: Symbol) -> Any:
        return self.find(name).vars[name]

    def define(self, name: Symbol, value: Any) -> None:
        self.vars[name] = value

    def set(self, name: Symbol, value: Any) -> None:
        self.find(name).vars[name] = value


@dataclass(slots=True)
class Lambda:
    params: Any          # list of Symbols, or a Symbol for variadic, or dotted
    body: Any            # list of expressions
    env: Env

    def bind(self, args: list[Any]) -> Env:
        vars: dict[Symbol, Any] = {}
        params = self.params
        i = 0
        while isinstance(params, Pair):
            if i >= len(args):
                raise LispError(f"too few arguments: expected {to_string(self.params)}")
            vars[params.car] = args[i]
            params = params.cdr
            i += 1
        if params is NIL:
            if i != len(args):
                raise LispError(f"too many arguments: expected {to_string(self.params)}, got {len(args)}")
        else:  # rest parameter
            vars[params] = lst(*args[i:])
        return Env(vars, self.env)


# --------------------------------------------------------------- primitives

def _check_num(*xs: Any) -> None:
    for x in xs:
        if isinstance(x, bool) or not isinstance(x, (int, float)):
            raise LispError(f"expected number, got {to_string(x)}")


def _arith(fn: Callable, identity: Any = None, name: str = "?") -> Callable:
    def prim(*args: Any) -> Any:
        _check_num(*args)
        if not args:
            if identity is None:
                raise LispError(f"{name}: expected at least one argument")
            return identity
        if len(args) == 1 and identity is not None and name in ("-", "/"):
            return fn(identity, args[0])
        acc = args[0]
        for a in args[1:]:
            acc = fn(acc, a)
        return acc
    prim.__name__ = name
    return prim


def _div(a: Any, b: Any) -> Any:
    if b == 0:
        raise LispError("division by zero")
    q = a / b
    return int(q) if isinstance(a, int) and isinstance(b, int) and a % b == 0 else q


def _compare(fn: Callable, name: str) -> Callable:
    def prim(*args: Any) -> bool:
        _check_num(*args)
        if len(args) < 2:
            raise LispError(f"{name}: expected at least two arguments")
        return all(fn(a, b) for a, b in zip(args, args[1:]))
    prim.__name__ = name
    return prim


def _car(p: Any) -> Any:
    if not isinstance(p, Pair):
        raise LispError(f"car: expected pair, got {to_string(p)}")
    return p.car


def _cdr(p: Any) -> Any:
    if not isinstance(p, Pair):
        raise LispError(f"cdr: expected pair, got {to_string(p)}")
    return p.cdr


def _length(x: Any) -> int:
    n = 0
    while isinstance(x, Pair):
        n += 1
        x = x.cdr
    if x is not NIL:
        raise LispError("length: not a proper list")
    return n


def _append(*lists: Any) -> Any:
    if not lists:
        return NIL
    out = lists[-1]
    for l in reversed(lists[:-1]):
        out = lst(*list(l), tail=out) if l is not NIL else out
    return out


def _eqv(a: Any, b: Any) -> bool:
    if isinstance(a, (int, float)) and isinstance(b, (int, float)) and not isinstance(a, bool) and not isinstance(b, bool):
        return a == b
    return a is b or (isinstance(a, str) and isinstance(b, str) and a == b)


def _equal(a: Any, b: Any) -> bool:
    if isinstance(a, Pair) and isinstance(b, Pair):
        return _equal(a.car, b.car) and _equal(a.cdr, b.cdr)
    return _eqv(a, b)


_output = sys.stdout


def _display(*args: Any) -> Any:
    _output.write("".join(a if isinstance(a, str) and not isinstance(a, Symbol) else to_string(a) for a in args))
    return NIL


def _newline() -> Any:
    _output.write("\n")
    return NIL


def _error(*args: Any) -> Any:
    raise LispError(" ".join(a if isinstance(a, str) and not isinstance(a, Symbol) else to_string(a) for a in args))


def standard_env() -> Env:
    env = Env()
    prims: dict[str, Any] = {
        "+": _arith(op.add, 0, "+"),
        "-": _arith(op.sub, 0, "-"),
        "*": _arith(op.mul, 1, "*"),
        "/": _arith(_div, 1, "/"),
        "=": _compare(op.eq, "="),
        "<": _compare(op.lt, "<"),
        ">": _compare(op.gt, ">"),
        "<=": _compare(op.le, "<="),
        ">=": _compare(op.ge, ">="),
        "modulo": lambda a, b: a % b,
        "remainder": lambda a, b: int(math.fmod(a, b)),
        "quotient": lambda a, b: int(a / b),
        "abs": abs, "min": min, "max": max,
        "sqrt": math.sqrt, "expt": lambda a, b: a ** b,
        "floor": lambda x: int(math.floor(x)), "round": lambda x: int(round(x)),
        "car": _car, "cdr": _cdr, "cons": Pair,
        "list": lambda *a: lst(*a),
        "length": _length, "append": _append,
        "reverse": lambda l: lst(*reversed(list(l))),
        "null?": lambda x: x is NIL,
        "pair?": lambda x: isinstance(x, Pair),
        "list?": lambda x: x is NIL or (isinstance(x, Pair) and _proper(x)),
        "symbol?": lambda x: isinstance(x, Symbol),
        "string?": lambda x: isinstance(x, str) and not isinstance(x, Symbol),
        "number?": lambda x: isinstance(x, (int, float)) and not isinstance(x, bool),
        "boolean?": lambda x: isinstance(x, bool),
        "procedure?": lambda x: isinstance(x, Lambda) or callable(x),
        "eq?": _eqv, "eqv?": _eqv, "equal?": _equal,
        "not": lambda x: x is False,
        "string-append": lambda *s: "".join(s),
        "string-length": len,
        "number->string": lambda n: to_string(n),
        "symbol->string": lambda s: str(s),
        "string->symbol": sym,
        "display": _display, "newline": _newline, "error": _error,
        "apply": None,  # filled in by evaluator (needs eval access)
        "map": None,
    }
    for name, fn in prims.items():
        if fn is not None:
            if not hasattr(fn, "__name__") or fn.__name__ == "<lambda>":
                try:
                    fn.__name__ = name
                except (AttributeError, TypeError):
                    pass
            env.define(sym(name), fn)
    env.define(sym("apply"), _make_apply())
    env.define(sym("map"), _make_map())
    return env


def _proper(x: Any) -> bool:
    while isinstance(x, Pair):
        x = x.cdr
    return x is NIL


def _make_apply() -> Callable:
    def apply_(fn: Any, *args: Any) -> Any:
        if not args:
            raise LispError("apply: expected a list argument")
        all_args = list(args[:-1]) + list(args[-1])
        return call(fn, all_args)
    apply_.__name__ = "apply"
    return apply_


def _make_map() -> Callable:
    def map_(fn: Any, *lists: Any) -> Any:
        if not lists:
            raise LispError("map: expected at least one list")
        pylists = [list(l) for l in lists]
        return lst(*(call(fn, list(items)) for items in zip(*pylists)))
    map_.__name__ = "map"
    return map_


# ---------------------------------------------------------------- evaluator

_QUOTE, _IF, _DEFINE, _SET, _LAMBDA, _BEGIN, _LET, _COND, _AND, _OR, _ELSE = (
    sym(s) for s in ("quote", "if", "define", "set!", "lambda", "begin", "let", "cond", "and", "or", "else")
)


def call(fn: Any, args: list[Any]) -> Any:
    if isinstance(fn, Lambda):
        env = fn.bind(args)
        return _eval_body(fn.body, env)
    if callable(fn):
        return fn(*args)
    raise LispError(f"not a procedure: {to_string(fn)}")


def _eval_body(body: Any, env: Env) -> Any:
    """Evaluate a sequence; the last expression is in tail position."""
    result: Any = NIL
    while isinstance(body, Pair):
        if body.cdr is NIL:
            return eval_(body.car, env)
        result = eval_(body.car, env)
        body = body.cdr
    return result


def eval_(x: Any, env: Env) -> Any:  # noqa: C901 - one big dispatch loop on purpose
    while True:
        if isinstance(x, Symbol):
            return env.lookup(x)
        if not isinstance(x, Pair):
            return x  # self-evaluating constant

        head = x.car
        if head is _QUOTE:
            return x.cdr.car
        if head is _IF:
            test = eval_(x.cdr.car, env)
            if test is not False:
                x = x.cdr.cdr.car
            else:
                rest = x.cdr.cdr.cdr
                if rest is NIL:
                    return NIL
                x = rest.car
            continue
        if head is _DEFINE:
            target = x.cdr.car
            if isinstance(target, Pair):  # (define (f . params) body...)
                env.define(target.car, Lambda(target.cdr, x.cdr.cdr, env))
            else:
                env.define(target, eval_(x.cdr.cdr.car, env))
            return target if isinstance(target, Symbol) else target.car
        if head is _SET:
            env.set(x.cdr.car, eval_(x.cdr.cdr.car, env))
            return NIL
        if head is _LAMBDA:
            return Lambda(x.cdr.car, x.cdr.cdr, env)
        if head is _BEGIN:
            body = x.cdr
            if body is NIL:
                return NIL
            while body.cdr is not NIL:
                eval_(body.car, env)
                body = body.cdr
            x = body.car
            continue
        if head is _LET:
            bindings = x.cdr.car
            names, vals = [], []
            for b in bindings:
                names.append(b.car)
                vals.append(eval_(b.cdr.car, env))
            env = Env(dict(zip(names, vals)), env)
            body = x.cdr.cdr
            while body.cdr is not NIL:
                eval_(body.car, env)
                body = body.cdr
            x = body.car
            continue
        if head is _COND:
            clause = x.cdr
            matched = False
            while isinstance(clause, Pair):
                c = clause.car
                if c.car is _ELSE or eval_(c.car, env) is not False:
                    matched = True
                    body = c.cdr
                    if body is NIL:
                        return True
                    while body.cdr is not NIL:
                        eval_(body.car, env)
                        body = body.cdr
                    x = body.car
                    break
                clause = clause.cdr
            if not matched:
                return NIL
            continue
        if head is _AND:
            rest = x.cdr
            if rest is NIL:
                return True
            while rest.cdr is not NIL:
                if eval_(rest.car, env) is False:
                    return False
                rest = rest.cdr
            x = rest.car
            continue
        if head is _OR:
            rest = x.cdr
            if rest is NIL:
                return False
            while rest.cdr is not NIL:
                v = eval_(rest.car, env)
                if v is not False:
                    return v
                rest = rest.cdr
            x = rest.car
            continue

        # procedure application
        fn = eval_(head, env)
        args = [eval_(a, env) for a in x.cdr]
        if isinstance(fn, Lambda):
            env = fn.bind(args)
            body = fn.body
            if body is NIL:
                return NIL
            while body.cdr is not NIL:
                eval_(body.car, env)
                body = body.cdr
            x = body.car
            continue  # proper tail call
        if callable(fn):
            return fn(*args)
        raise LispError(f"not a procedure: {to_string(fn)}")


# --------------------------------------------------------------------- API

def run(src: str, env: Env | None = None) -> Any:
    """Evaluate every form in `src`; return the value of the last one."""
    env = env if env is not None else standard_env()
    result: Any = NIL
    for form in parse_all(src):
        result = eval_(form, env)
    return result


def repl() -> None:
    env = standard_env()
    print("minilisp — Ctrl-D to exit")
    buf = ""
    while True:
        try:
            line = input("... " if buf else "> ")
        except EOFError:
            print()
            return
        buf += line + "\n"
        if buf.count("(") > buf.count(")"):
            continue  # keep reading a multi-line form
        try:
            for form in parse_all(buf):
                val = eval_(form, env)
                if val is not NIL:
                    print(to_string(val))
        except LispError as e:
            print(f"error: {e}")
        except RecursionError:
            print("error: recursion depth exceeded")
        buf = ""


if __name__ == "__main__":
    if len(sys.argv) > 1:
        with open(sys.argv[1]) as f:
            try:
                run(f.read())
            except LispError as e:
                print(f"error: {e}", file=sys.stderr)
                sys.exit(1)
    else:
        repl()
