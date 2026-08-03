# MarkovText

A small, dependency-free Markov chain text generator in pure Python.
Train on any corpus and generate plausible-sounding new text that mimics
its word patterns.

Everything is stdlib — no installation of third-party packages required to
*use* it (only `pytest` to run the tests, and that's optional).

## How it works

A Markov model records *n-grams*: for every sequence of `order` words, it
remembers which words came next and how often. Generation walks the chain,
and at each step picks the next word based on the transitions observed in
training. Higher orders produce text that more closely mirrors the source
(and eventually starts copying whole phrases); order 2–3 is a good default.

## Install

```sh
pip install .          # installs the `markovtext` command + package
# or, without installing:
python -m markov.cli ...
```

## Usage

Train on a corpus (documents separated by blank lines):

```sh
markovtext train sample/grimms_fables.txt -o model.json
# trained: 10 document(s), 414 unique words -> model.json
```

Tune the order and weighting:

```sh
markovtext train corpus.txt -n 3                  # 3-gram model
markovtext train corpus.txt --uniform             # ignore word frequencies
```

Generate text:

```sh
markovtext generate model.json --max-words 40 --count 5
markovtext generate model.json --seed 42          # reproducible output
```

### As a library

```python
from markov import MarkovModel, train_on_text

model = MarkovModel(order=2)
train_on_text(model, open("corpus.txt").read())
print(model.generate(max_words=50, seed="anything"))
```

## CLI reference

| Command | Flag | Meaning |
| --- | --- | --- |
| `train` | `-o, --output` | output JSON path (default `model.json`) |
| | `-n, --order` | n-gram order, >= 1 (default 2) |
| | `--uniform` | pick continuations uniformly instead of by frequency |
| `generate` | `--max-words` | max words per sample (default 50) |
| | `--count` | number of samples to print (default 1) |
| | `--seed` | random seed for repeatable output |

## Development

```sh
python -m venv .venv && .venv/bin/pip install pytest
.venv/bin/python -m pytest -q
```

## License

MIT
