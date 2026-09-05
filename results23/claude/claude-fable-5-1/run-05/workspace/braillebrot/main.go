// braillebrot renders the Mandelbrot set in a terminal using Unicode braille
// characters. Each character cell packs a 2x4 grid of dots, so an 80x24
// terminal gives a 160x96 pixel image. Color comes from the smooth iteration
// count (Renormalized escape time), mapped onto a cyclic palette.
package main

import (
	"bufio"
	"flag"
	"fmt"
	"math"
	"math/cmplx"
	"os"
)

// Braille dot bit positions, indexed [row][col] for a 4-row, 2-col cell.
// See U+2800 block layout: dots 1-3 left column, 4-6 right column,
// 7 bottom-left, 8 bottom-right.
var brailleBits = [4][2]rune{
	{0x01, 0x08},
	{0x02, 0x10},
	{0x04, 0x20},
	{0x40, 0x80},
}

// escape returns the smooth (fractional) iteration count for c, or -1 if the
// point never escaped within maxIter.
func escape(c complex128, maxIter int) float64 {
	// Cheap interior tests: main cardioid and period-2 bulb. These regions
	// are known to be in the set, so skip iterating them.
	x, y := real(c), imag(c)
	q := (x-0.25)*(x-0.25) + y*y
	if q*(q+(x-0.25)) <= 0.25*y*y {
		return -1
	}
	if (x+1)*(x+1)+y*y <= 0.0625 {
		return -1
	}

	var z complex128
	for i := 0; i < maxIter; i++ {
		z = z*z + c
		if r2 := real(z)*real(z) + imag(z)*imag(z); r2 > 256 {
			// Renormalized iteration count: i + 1 - log(log|z|)/log 2.
			mod := cmplx.Abs(z)
			return float64(i) + 1 - math.Log(math.Log(mod))/math.Ln2
		}
	}
	return -1
}

// palette maps a smooth iteration value to an RGB triple using offset sine
// waves, which gives a pleasant cyclic gradient without a lookup table.
func palette(t float64) (int, int, int) {
	// Slow the cycle so bands don't alias badly at low iteration counts.
	t = t * 0.12
	r := 0.5 + 0.5*math.Sin(t+0.0)
	g := 0.5 + 0.5*math.Sin(t+2.1)
	b := 0.5 + 0.5*math.Sin(t+4.2)
	return int(r * 255), int(g * 255), int(b * 255)
}

type view struct {
	cx, cy float64 // center
	scale  float64 // width of the view in the complex plane
}

// render draws the set into a grid of cols x rows character cells and
// writes ANSI-colored braille to w.
func render(w *bufio.Writer, v view, cols, rows, maxIter int, color bool) {
	pw, ph := cols*2, rows*4 // pixel dimensions
	// Terminal cells are roughly twice as tall as wide, so a braille cell
	// (2 wide, 4 tall in dots) is close to square in dot-space already.
	// Just keep the complex-plane aspect equal to the pixel aspect.
	dx := v.scale / float64(pw)
	dy := dx
	x0 := v.cx - v.scale/2
	y0 := v.cy + dy*float64(ph)/2

	for row := 0; row < rows; row++ {
		for col := 0; col < cols; col++ {
			var glyph rune = 0x2800
			var sum float64
			var n int
			for py := 0; py < 4; py++ {
				for px := 0; px < 2; px++ {
					x := x0 + dx*float64(col*2+px)
					y := y0 - dy*float64(row*4+py)
					e := escape(complex(x, y), maxIter)
					if e >= 0 {
						// Dot ON = outside the set; the set itself is
						// left dark, which reads as a silhouette.
						glyph |= brailleBits[py][px]
						sum += e
						n++
					}
				}
			}
			if color && n > 0 {
				r, g, b := palette(sum / float64(n))
				fmt.Fprintf(w, "\x1b[38;2;%d;%d;%dm%c", r, g, b, glyph)
			} else {
				w.WriteRune(glyph)
			}
		}
		if color {
			w.WriteString("\x1b[0m")
		}
		w.WriteByte('\n')
	}
}

func main() {
	cols := flag.Int("w", 100, "width in character cells")
	rows := flag.Int("h", 36, "height in character cells")
	maxIter := flag.Int("iter", 200, "maximum iterations")
	cx := flag.Float64("x", -0.6, "center real part")
	cy := flag.Float64("y", 0.0, "center imaginary part")
	scale := flag.Float64("scale", 3.2, "width of view in the complex plane")
	noColor := flag.Bool("no-color", false, "disable ANSI truecolor output")
	flag.Parse()

	if *cols <= 0 || *rows <= 0 || *maxIter <= 0 || *scale <= 0 {
		fmt.Fprintln(os.Stderr, "width, height, iter and scale must be positive")
		os.Exit(2)
	}

	w := bufio.NewWriterSize(os.Stdout, 1<<16)
	defer w.Flush()
	render(w, view{*cx, *cy, *scale}, *cols, *rows, *maxIter, !*noColor)
}
