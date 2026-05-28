"""Render the Mandelbrot set to the terminal with truecolor ANSI."""

import math
import sys


def mandelbrot(c: complex, max_iter: int = 200) -> float:
    z = 0j
    for n in range(max_iter):
        z = z * z + c
        if (mag := abs(z)) > 2:
            # smooth iteration count — removes integer-banding
            return n + 1 - math.log(math.log(mag)) / math.log(2)
    return float(max_iter)


def color(t: float) -> tuple[int, int, int]:
    # palette inspired by Inigo Quilez's cosine gradients
    a = (0.5, 0.5, 0.5)
    b = (0.5, 0.5, 0.5)
    c = (1.0, 1.0, 1.0)
    d = (0.00, 0.10, 0.20)
    rgb = tuple(
        max(0, min(1, a[i] + b[i] * math.cos(2 * math.pi * (c[i] * t + d[i]))))
        for i in range(3)
    )
    return tuple(int(v * 255) for v in rgb)


def render(
    width: int = 120,
    height: int = 40,
    center: complex = -0.75 + 0j,
    zoom: float = 1.3,
    max_iter: int = 200,
) -> str:
    # terminal cells are ~2x taller than wide → squash y
    aspect = (width / height) * 0.5
    out = []
    for j in range(height):
        for i in range(width):
            x = (i / width - 0.5) * 3.0 * aspect / zoom + center.real
            y = (j / height - 0.5) * 3.0 / zoom + center.imag
            n = mandelbrot(complex(x, y), max_iter)
            if n >= max_iter:
                out.append("\033[38;2;0;0;0m \033[0m")
            else:
                t = math.sqrt(n / max_iter)
                r, g, b = color(t)
                out.append(f"\033[38;2;{r};{g};{b}m█\033[0m")
        out.append("\n")
    return "".join(out)


def render_ascii(
    width: int = 100,
    height: int = 36,
    center: complex = -0.75 + 0j,
    zoom: float = 1.3,
    max_iter: int = 100,
) -> str:
    ramp = " .`':,;-~+*=xX#%@"
    aspect = (width / height) * 0.5
    out = []
    for j in range(height):
        for i in range(width):
            x = (i / width - 0.5) * 3.0 * aspect / zoom + center.real
            y = (j / height - 0.5) * 3.0 / zoom + center.imag
            n = mandelbrot(complex(x, y), max_iter)
            if n >= max_iter:
                out.append(" ")
            else:
                idx = min(len(ramp) - 1, int(math.sqrt(n / max_iter) * (len(ramp) - 1)))
                out.append(ramp[idx])
        out.append("\n")
    return "".join(out)


if __name__ == "__main__":
    mode = sys.argv[1] if len(sys.argv) > 1 else "ascii"
    if mode == "color":
        sys.stdout.write(render())
    else:
        sys.stdout.write(render_ascii())
    sys.stdout.write("\n  Mandelbrot set — c ∈ ℂ where z_{n+1} = z_n² + c stays bounded\n")
