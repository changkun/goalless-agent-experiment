# pwgen

A small, dependency-free security tool that generates **passwords** (random
characters) and **passphrases** (random words), driven by the OS cryptographic
random source, and reports the entropy of what it produces.

Built as a demonstration of secure-by-default generation + honest entropy
accounting. No pip install needed — plain Python 3.7+ stdlib.

## Usage

```
python3 pwgen.py pw -l 18                # 18-char random password
python3 pwgen.py pw -l 24 --no-symbols   # alnum only
python3 pwgen.py pw --exclude-ambiguous  # drop 0 O 1 l I |
python3 pwgen.py pw --estimate           # also print a heuristic strength check

python3 pwgen.py phrase -w 5             # 5-word passphrase: brick-tiger-...
python3 pwgen.py phrase -w 4 -t          # capitalised: Kite-Lunar-Raven-Tiger

python3 pwgen.py estimate "correct horse battery staple"
```

Run `python3 pwgen.py -h` or `python3 pwgen.py <sub> -h` for all options.

## What makes it secure

- **CSPRNG source.** Uses `secrets` (backed by the OS `/dev/urandom`), never
  the Mersenne Twister / `random`.
- **Unbiased sampling.** `urandom_int` maps a random byte to `[0, n)` by
  rejection sampling, so no character is over- or under-represented even when
  the class size isn't a power of two.
- **Guaranteed classes.** Enabled classes each contribute at least one
  character, then a final Fisher–Yates shuffle keeps the result uniform over
  the constrained space — so "has a digit" never silently fails.
- **Real entropy math.** For a passphrase, entropy = log2(wordlist size) per
  word, and the wordlist is counted exactly. No inflated "51 bits" from an
  assumed-7776 Diceware list.

## Honesty about strength

The generator's entropy figure (`log2(charset ** length)`) is exact **for a
uniform random draw**. Most real-world passwords fail because they are *not*
uniform random (a word + a year, a leetspeak name, a reused phrase). The
`estimate` subcommand is an intentionally conservative *upper bound* that
flags a dictionary-derived pattern; treat anything it says below ~70 bits as
reason to generate instead of hand-crafting.

## Layout

- `pwgen.py` — the tool (`python3 pwgen.py`)
- `test_pwgen.py` — unittest-style suite, no pytest required

```
python3 test_pwgen.py
```
