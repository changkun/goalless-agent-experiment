# passgen

A dependency-free password, token, and passphrase generator with an encrypted
vault. Built entirely on the Python standard library — no third-party packages.

## Features

- **`generate`** — random passwords with tunable character sets and length.
- **`token`** — high-entropy tokens / API keys from a custom alphabet.
- **`passphrase`** — Diceware-style passphrases from a wordlist.
- **`info`** — show pool size and entropy for your settings.
- **`vault`** — store secrets in a file encrypted with ChaCha20-Poly1305.

## Install

No installation is required. Run from the repo root:

```bash
python3 -m passgen generate
```

To install as a command, use pip:

```bash
pip install .
passgen generate -l 24
```

## Usage

```bash
# Generate a 24-character password including all character classes
passgen generate -l 24

# Exclude ambiguous characters (Il1O0)
passgen generate --no-ambiguous

# Generate a 64-character API token
passgen token -l 64

# Diceware-style passphrase with 8 words
passgen passphrase -w 8

# Entropy audit for a given setting
passgen info -l 16
```

### Encrypted vault

The vault stores entries as key/value maps in a single encrypted file.
Encryption uses ChaCha20-Poly1305 (RFC 8439) with PBKDF2-HMAC-SHA256
password stretching, implemented from scratch on the stdlib.

```bash
# Create a new vault (prompts for a master password)
passgen vault init

# Add an entry (auto-generates a password if none supplied)
passgen vault add github username=octocat

# Show an entry
passgen vault get github

# List entry names
passgen vault list

# Delete an entry
passgen vault delete github

# Change the master password
passgen vault setpass -f myvault.json
```

By default the vault file is `./vault.json`; override with `-f path` or the
`PASSGEN_VAULT` environment variable.

## API

```python
from passgen import PasswordConfig, generate_password, generate_passphrase
from passgen.core import generate_token, entropy

pw = generate_password(PasswordConfig(length=20, symbols=False))
phrase = generate_passphrase(words=6)
token = generate_token(length=48)
bits = entropy(pool_size=94, length=16)
```

## Tests

```bash
python3 -m unittest discover -s tests -v
```

The cipher is validated against the official RFC 8439 test vectors
(Sections 2.5.2 and 2.8.2).
