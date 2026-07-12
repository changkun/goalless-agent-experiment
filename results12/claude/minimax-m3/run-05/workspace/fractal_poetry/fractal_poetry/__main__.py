"""Entrypoint: print a Mandelbrot set with a fractal poem beneath it."""

from .mandel import render
from .poem import recite


def main() -> None:
    print(render())
    print()
    print(recite())


if __name__ == "__main__":
    main()
