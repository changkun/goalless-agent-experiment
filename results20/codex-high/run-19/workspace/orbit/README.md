# orbit

A tiny, dependency-free ASCII solar-system explorer written in Python.

## Usage

```bash
# Show every planet
python -m orbit

# Show specific planet(s)
python -m orbit mars jupiter

# Unknown names are reported to stderr
python -m orbit pluto
```

## Install (optional)

```bash
pip install -e .
orbit jupiter
```

## Test

```bash
python -m unittest discover -s tests -v
```

## Example

```
5. Jupiter
   Diameter : 142,984 km  ########################
   Year     : 4,331.6 days
   Moons    : 95
   Did you know? So big that all other planets could fit inside.
```
