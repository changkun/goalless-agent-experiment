# passgen

A tiny, dependency-free CLI for generating strong **passphrases** and
**passwords**, with per-result entropy information.

## Install

```sh
cd passgen
pip install -e .
```

## Usage

Generate a passphrase (default):

```sh
passgen -w 5
# e.g. slate-jade-kelp-ember-tiger
```

Show entropy:

```sh
passgen -v -w 5
# slate-jade-kelp-ember-tiger  (28.5 bits)
```

Generate a 16-character password:

```sh
passgen --password -l 16
```

Options:

| Flag | Meaning |
| --- | --- |
| `-w N` | Number of words in a passphrase |
| `-l N` | Password length |
| `-s SEP` | Passphrase separator (default `-`) |
| `--capitalize` | Capitalize each passphrase word |
| `--number` | Append a 2-digit number to the passphrase |
| `--password` | Generate a password instead |
| `--no-lower/--no-upper/--no-digits/--no-symbols` | Disable password character classes |
| `-n N` | Generate N values |
| `-v` | Show entropy in bits for each result |

## Library

```python
from passgen import generate_passphrase, generate_password, entropy

p = generate_passphrase(5)
pw = generate_password(16)
print(entropy(100, 5))  # -> 28.5
```

Entropy is computed as `length * log2(pool_size)`. This reflects the strength
of the random draw, assuming a secure RNG (`secrets`).

## Tests

```sh
cd passgen
python -m unittest discover -s tests -v
```
