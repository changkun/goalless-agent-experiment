"""The tinylisp evaluator: special forms, macros, and tail-call elimination."""

from __future__ import annotations

from typing import Any, List, Optional, Tuple

from .types import Environment, Keyword, LispError, Procedure, Symbol

SPECIAL_FORMS = frozenset(
    {
        "quote",
        "quasiquote",
        "unquote",
        "unquote-splicing",
        "if",
        "cond",
        "when",
        "unless",
        "and",
        "or",
        "def",
        "set!",
        "let",
        "fn",
        "lambda",
        "defn",
        "defmacro",
        "do",
        "while",
        "try",
        "quit",
    }
)


def is_truthy(value: Any) -> bool:
    return value is not None and value is not False


def parse_params(spec: Any) -> Tuple[List[Symbol], Optional[Symbol]]:
    """Split a parameter list into fixed names plus an optional ``&rest`` name."""
    if not isinstance(spec, list):
        raise LispError("parameter list must be a list")
    params: List[Symbol] = []
    rest: Optional[Symbol] = None
    index = 0
    while index < len(spec):
        name = spec[index]
        if not isinstance(name, Symbol):
            raise LispError(f"parameter names must be symbols, got {name!r}")
        if name == "&":
            if index + 2 != len(spec):
                raise LispError("'&' must be followed by exactly one name")
            tail = spec[index + 1]
            if not isinstance(tail, Symbol):
                raise LispError("rest parameter must be a symbol")
            rest = tail
            break
        params.append(name)
        index += 1
    return params, rest


def make_procedure(
    args: List[Any], env: Environment, name: str, is_macro: bool = False
) -> Procedure:
    if not args:
        raise LispError(f"{name} needs a parameter list")
    params, rest = parse_params(args[0])
    body = list(args[1:]) or [None]
    return Procedure(params, rest, body, env, name=name, is_macro=is_macro)


def expand_quasiquote(form: Any, env: Environment) -> Any:
    if not isinstance(form, list):
        return form
    if len(form) == 2 and form[0] == Symbol("unquote"):
        return evaluate(form[1], env)
    out: List[Any] = []
    for item in form:
        if (
            isinstance(item, list)
            and len(item) == 2
            and item[0] == Symbol("unquote-splicing")
        ):
            spliced = evaluate(item[1], env)
            if not isinstance(spliced, list):
                raise LispError("unquote-splicing expects a list")
            out.extend(spliced)
        else:
            out.append(expand_quasiquote(item, env))
    return out


def evaluate(expr: Any, env: Environment) -> Any:
    """Evaluate ``expr`` in ``env``, looping instead of recursing on tail calls."""
    while True:
        if isinstance(expr, Symbol):
            return env.lookup(expr)
        if isinstance(expr, (Keyword, str, int, float, bool)) or expr is None:
            return expr
        if not isinstance(expr, list):
            return expr
        if not expr:
            return []

        head = expr[0]
        args = expr[1:]

        if isinstance(head, Symbol) and head in SPECIAL_FORMS:
            if head == "quote":
                return args[0] if args else None
            if head == "quasiquote":
                return expand_quasiquote(args[0] if args else None, env)
            if head in ("unquote", "unquote-splicing"):
                raise LispError(f"{head} outside of quasiquote")

            if head == "if":
                if not 2 <= len(args) <= 3:
                    raise LispError("if expects 2 or 3 arguments")
                if is_truthy(evaluate(args[0], env)):
                    expr = args[1]
                    continue
                if len(args) == 3:
                    expr = args[2]
                    continue
                return None

            if head == "cond":
                if len(args) % 2 != 0:
                    raise LispError("cond expects an even number of forms")
                chosen = None
                matched = False
                for index in range(0, len(args), 2):
                    test = args[index]
                    if test == Symbol("else") or is_truthy(evaluate(test, env)):
                        chosen = args[index + 1]
                        matched = True
                        break
                if not matched:
                    return None
                expr = chosen
                continue

            if head in ("when", "unless"):
                if not args:
                    raise LispError(f"{head} expects a test")
                test = is_truthy(evaluate(args[0], env))
                if head == "unless":
                    test = not test
                if not test or len(args) == 1:
                    return None
                for form in args[1:-1]:
                    evaluate(form, env)
                expr = args[-1]
                continue

            if head == "and":
                if not args:
                    return True
                for form in args[:-1]:
                    value = evaluate(form, env)
                    if not is_truthy(value):
                        return value
                expr = args[-1]
                continue

            if head == "or":
                if not args:
                    return None
                for form in args[:-1]:
                    value = evaluate(form, env)
                    if is_truthy(value):
                        return value
                expr = args[-1]
                continue

            if head == "def":
                if len(args) != 2 or not isinstance(args[0], Symbol):
                    raise LispError("def expects a symbol and a value")
                value = evaluate(args[1], env)
                if isinstance(value, Procedure) and value.name == "lambda":
                    value.name = str(args[0])
                return env.define(args[0], value)

            if head == "set!":
                if len(args) != 2 or not isinstance(args[0], Symbol):
                    raise LispError("set! expects a symbol and a value")
                return env.set(args[0], evaluate(args[1], env))

            if head == "let":
                if not args or not isinstance(args[0], list):
                    raise LispError("let expects a binding list")
                bindings = args[0]
                if len(bindings) % 2 != 0:
                    raise LispError("let bindings must be name/value pairs")
                scope = Environment(parent=env)
                for index in range(0, len(bindings), 2):
                    name = bindings[index]
                    if not isinstance(name, Symbol):
                        raise LispError("let binding names must be symbols")
                    scope.vars[name] = evaluate(bindings[index + 1], scope)
                body = args[1:]
                if not body:
                    return None
                for form in body[:-1]:
                    evaluate(form, scope)
                expr, env = body[-1], scope
                continue

            if head in ("fn", "lambda"):
                return make_procedure(args, env, "lambda")

            if head == "defn":
                if len(args) < 2 or not isinstance(args[0], Symbol):
                    raise LispError("defn expects a name and a parameter list")
                proc = make_procedure(args[1:], env, str(args[0]))
                return env.define(args[0], proc)

            if head == "defmacro":
                if len(args) < 2 or not isinstance(args[0], Symbol):
                    raise LispError("defmacro expects a name and a parameter list")
                macro = make_procedure(args[1:], env, str(args[0]), is_macro=True)
                return env.define(args[0], macro)

            if head == "do":
                if not args:
                    return None
                for form in args[:-1]:
                    evaluate(form, env)
                expr = args[-1]
                continue

            if head == "while":
                if not args:
                    raise LispError("while expects a test")
                result = None
                while is_truthy(evaluate(args[0], env)):
                    for form in args[1:]:
                        result = evaluate(form, env)
                return result

            if head == "try":
                if len(args) != 2 or not isinstance(args[1], list):
                    raise LispError("try expects a body and a (catch name ...) form")
                catch = args[1]
                if len(catch) < 2 or catch[0] != Symbol("catch"):
                    raise LispError("try expects a (catch name ...) handler")
                name = catch[1]
                if not isinstance(name, Symbol):
                    raise LispError("catch expects a symbol to bind the error")
                try:
                    return evaluate(args[0], env)
                except LispError as error:
                    payload = error.args[0] if error.args else str(error)
                    scope = Environment({name: payload}, parent=env)
                    result = None
                    for form in catch[2:]:
                        result = evaluate(form, scope)
                    return result

            if head == "quit":
                raise SystemExit(0)

        procedure = evaluate(head, env)

        if isinstance(procedure, Procedure) and procedure.is_macro:
            expr = apply_procedure(procedure, list(args))
            continue

        values = [evaluate(arg, env) for arg in args]

        if isinstance(procedure, Procedure):
            scope = procedure.bind(values)
            for form in procedure.body[:-1]:
                evaluate(form, scope)
            expr, env = procedure.body[-1], scope
            continue

        if callable(procedure):
            return procedure(*values)

        raise LispError(f"not callable: {procedure!r}")


def apply_procedure(procedure: Any, args: List[Any]) -> Any:
    """Call a builtin or user procedure with already-evaluated arguments."""
    if isinstance(procedure, Procedure):
        scope = procedure.bind(list(args))
        result = None
        for form in procedure.body:
            result = evaluate(form, scope)
        return result
    if callable(procedure):
        return procedure(*args)
    raise LispError(f"not callable: {procedure!r}")
