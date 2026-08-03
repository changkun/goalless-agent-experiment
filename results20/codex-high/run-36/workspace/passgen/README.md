# passgen

A small, dependency-free Python CLI for generating secure passwords and
analyzing their strength. Built only on the Python standard library
(`secrets`, `argparse`, `unittest`), so there's nothing to install.

## Features

- Cryptographically secure generation via `secrets`
- Guarantees each enabled character group is represented
- Optional exclusion of ambiguous characters (`Il1O0o`)
- Password strength analyzer with entropy (bits) and a simple grade
- Optional colorized output

## Usage

Generate a 16-character password (default):

```bash
python3 -m passgen
```

More control:

```bash
python3 -m passgen --length 24 --no-ambiguous
python3 -m passgen --nosymbols
python3 -m passgen --count 5 --length 12
```

Analyze a password:

```bash
python3 -m passgen "JustAPassword1!"
# or prompt (hidden input)
python3 -m passgen --analyze
```

### Options

| Flag | Description |
| --- | --- |
| `-n, --length` | Password length (default `16`) |
| `--no-lowercase` / `--no-uppercase` | Exclude a case group |
| `--no-digits` / `--no-symbols` | Exclude a group |
| `--no-ambiguous` | Drop `Il1O0o` from the pool |
| `--count N` | Generate N passwords |
| `--analyze` | Read a password from a hidden prompt |
| `--no-color` | Disable colored output |

## Library API

```python
from passgen import generate_password, analyze_strength

pw = generate_password(length=20, exclude_ambiguous=True)
info = analyze_strength(pw)
print(info["grade"], info["entropy_bits"])
```

## Tests

```bash
python3 -m unittest discover -s tests -v
```

## Install (optional)

```bash
python3 -m pip install -e .   # provides the `passgen` command
```
