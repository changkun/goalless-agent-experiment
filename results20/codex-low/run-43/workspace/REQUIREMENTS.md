# 2048 CLI

A dependency-free terminal implementation of 2048 in pure Python.

## Usage

Run `python3 -m game2048` and play with the arrow keys (W/A/S/D also work).

## Structure

- `game2048/__init__.py` — package metadata / version
- `game2048/logic.py` — pure game logic (no I/O)
- `game2048/__main__.py` — terminal UI entry point

## Tests

Run `python3 -m unittest discover -s tests -v`
