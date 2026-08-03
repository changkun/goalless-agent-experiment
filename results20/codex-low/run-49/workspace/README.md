# passgen

A minimal, dependency-free passphrase generator written in pure Python.

## Usage

Run from the repository root:

```bash
python3 -m passgen                  # six words, "-" separator
python3 -m passgen -n 4             # four words
python3 -m passgen -n 7 -s "_"      # custom separator
python3 -m passgen --entropy        # also print approximate entropy
```

## Safety notes

- Words are drawn without replacement using `secrets.randbelow`, which is
  backed by the platform's best available entropy source (CSPRNG).
- The bundled 254-word list is curated so each word is lowercase,
  unambiguous, and easy to spell and type. It is **not** a diceware-grade
  list, so don't rely on this for high-stakes secret-generation; treat it as
  a convenient utility.
- Approximate entropy is `count * floor(log2(pool_size))` bits.

## Tests

```bash
python3 -m unittest discover -s passgen/tests -v
```
