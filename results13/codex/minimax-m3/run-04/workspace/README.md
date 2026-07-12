# mandelbrot.py

A tiny, dependency-free Mandelbrot explorer for the terminal.

## Quick start

```bash
# Interactive: arrows / hjkl pan, +/- zoom, r reset, s save, q quit
python3 mandelbrot.py

# Headless ASCII print
python3 mandelbrot.py --no-interactive --width 100 --height 40

# Render an image (PNG if Pillow is installed, else PPM)
python3 mandelbrot.py --render out.png --width 1280 --height 720 --max-iter 1000
```

## Controls

| Key            | Action              |
| -------------- | ------------------- |
| arrows / hjkl  | pan                 |
| `+` / `-`      | zoom in / out       |
| `r`            | reset view          |
| `s`            | save `mandelbrot.png` |
| `q` / `Esc`    | quit                |

## Tests

```bash
python3 -m unittest test_mandelbrot.py -v
```
