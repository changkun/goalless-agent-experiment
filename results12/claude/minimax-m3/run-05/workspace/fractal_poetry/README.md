# fractal-poetry

A small Python package that prints an ASCII Mandelbrot set and layers
a self-similar poem beneath it. The poem and the fractal share a
structure: each part is the whole made smaller, and the whole is each
part made larger.

## Run it

```
python -m fractal_poetry
```

Or import the parts:

```python
from fractal_poetry import render, recite
print(render(width=100, height=40))
print(recite())
```

## Test it

```
python -m pytest -q
```

## Why

Because today is 2026-07-12 and the workspace was empty, and a
coastline is a kind of question you can ask a number.
