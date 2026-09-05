# minilisp

A small Scheme-flavoured Lisp interpreter in a single Python file, no dependencies.

    python3 minilisp.py            # REPL
    python3 minilisp.py demo.lisp  # run a file
    python3 -m unittest test_minilisp

## What it supports

- Data: integers, floats, strings, `#t`/`#f`, symbols, proper and dotted lists
- Special forms: `quote`, `if`, `define` (both forms), `set!`, `lambda` (fixed,
  variadic and dotted parameter lists), `begin`, `let`, `cond`/`else`, `and`, `or`
- Lexical closures with mutable captured variables
- Proper tail calls through `if`, `cond`, `let`, `begin`, `and`, `or` and
  procedure application, so loops written as tail recursion run in constant stack
- Primitives: arithmetic and comparison, `car`/`cdr`/`cons`/`list`/`length`/
  `append`/`reverse`/`map`/`apply`, type predicates, `eq?`/`eqv?`/`equal?`,
  string helpers, `display`/`newline`/`error`

## Layout

- `minilisp.py` reader, printer, environment, evaluator, primitives, REPL
- `test_minilisp.py` 30 unit tests covering the reader, special forms,
  tail calls, list operations and a few whole programs
- `demo.lisp` a sieve, a closure-based bank account, Church numerals

## Design notes

The evaluator is one `while True` loop that rewrites `x` and `env` for anything
in tail position and only recurses for sub-expressions that are not. Symbols
are interned `str` subclasses so special-form dispatch is identity comparison.
The empty list is a singleton that is truthy (only `#f` is false) and iterates
as empty so primitives can treat it uniformly with pairs.
