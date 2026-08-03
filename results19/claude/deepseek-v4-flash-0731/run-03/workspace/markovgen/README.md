# markovgen

An **order‑N Markov chain text generator** with a tiny, dependency‑free API and
a matching command‑line tool. Learn transition probabilities from example text,
then generate plausible‑sounding (if nonsensical) continuations.

## Quick start

```bash
python -m markovgen corpus.txt -n 2 -l 50
```

## Installation

No external runtime dependencies. Clone and, optionally, install as a package
to get the `markovgen` console command:

```bash
pip install -e .[dev]     # includes pytest for the test suite
```

## Library usage

```python
from markovgen import MarkovChain

chain = MarkovChain(order=2)
chain.fit("the cat sat the cat ran the cat sat")

print(chain.generate(20))                 # arbitrary start
print(chain.generate(8, seed=["the"]))    # anchored start
```

### Key concepts

- **Order** — how many preceding tokens form the context. Higher orders
  produce more coherent output but are more likely to stall at a dead end.
- **Greedy + weighted tie‑break** — a context's next token is the one seen most
  often; when several tie, one is sampled proportionally to its count. Feed a
  fixed `random.Random(...)` to the constructor for reproducible output.
- **`seed`** — an optional starting context. It's matched by *suffix*: give
  fewer tokens than `order` and generation anchors off the tail you provided.

### API reference

| Member | Description |
| --- | --- |
| `MarkovChain(order=2, rng=None)` | Construct a chain. `order >= 1`. |
| `.fit(texts)` | Learn from one `str` or an iterable of documents. Returns `self`. |
| `.generate(length, seed=None)` | Return a `str` of up to `length` tokens. |
| `.token_count` | Tokens seen during fitting. |
| `.start_count` | Distinct start contexts. |
| `.transition_count` | Distinct (context, next) pairs. |

## CLI

```
usage: markovgen [-h] [-n N] [-l N] [-s TOKEN [TOKEN ...]] [--seed INT] [corpus ...]

positional arguments:
  corpus                Text file(s) to learn from. Reads stdin if none given.

options:
  -n, --order N         Markov chain order, default 2
  -l, --length N        Number of tokens to generate, default 50
  -s, --seed-tokens     Starting tokens (matched by tail)
  --seed INT            Random seed for reproducible output
```

Examples:

```bash
echo "drink more water drink more coffee drink more tea" \
  | python -m markovgen -l 6 --seed drink
python -m markovgen hamlet.txt king_lear.txt -n 3 -l 100 --seed 7
```

## Tests

```bash
python -m pytest
```
