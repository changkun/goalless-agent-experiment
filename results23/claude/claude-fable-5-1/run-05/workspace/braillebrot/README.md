# braillebrot

Renders the Mandelbrot set in a terminal using Unicode braille characters
(U+2800 block). Each character cell packs a 2x4 grid of dots, so an 80x24
terminal shows a 160x96 pixel image. Dots are lit for points *outside* the
set, so the set itself appears as a dark silhouette. Color comes from the
renormalized (smooth) escape time, mapped onto a cyclic sine palette and
emitted as 24-bit ANSI color.

## Build and run

```sh
go build -o braillebrot .
./braillebrot                       # default view of the whole set
./braillebrot -w 120 -h 40 -iter 500
./braillebrot -no-color             # plain braille, pipe-friendly
```

## Flags

| flag        | default | meaning                                   |
|-------------|---------|-------------------------------------------|
| `-w`, `-h`  | 100, 36 | width and height in character cells       |
| `-iter`     | 200     | maximum iterations before assuming inside |
| `-x`, `-y`  | -0.6, 0 | center of the view in the complex plane   |
| `-scale`    | 3.2     | width of the view in the complex plane    |
| `-no-color` | false   | disable ANSI truecolor output             |

## Places worth visiting

```sh
# Seahorse valley
./braillebrot -x -0.745 -y 0.1 -scale 0.02 -iter 600

# A mini-Mandelbrot in the northern antenna region
./braillebrot -x -0.1592 -y -1.0317 -scale 0.06 -iter 400

# Elephant valley
./braillebrot -x 0.2925 -y 0.0150 -scale 0.03 -iter 500

# Spiral near the main antenna
./braillebrot -x -1.7495 -y 0 -scale 0.01 -iter 800
```

Higher `-iter` reveals more detail at deep zooms but costs time; the interior
of the main cardioid and the period-2 bulb are detected analytically so those
regions are free.

## Tests

```sh
go test ./...
```
