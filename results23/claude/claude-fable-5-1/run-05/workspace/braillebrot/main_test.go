package main

import (
	"bufio"
	"bytes"
	"strings"
	"testing"
	"unicode/utf8"
)

func TestEscapeInterior(t *testing.T) {
	// Points well inside the set never escape.
	for _, c := range []complex128{0, -1, complex(-0.1, 0.7), complex(-1.75, 0)} {
		if e := escape(c, 500); e != -1 {
			t.Errorf("escape(%v) = %v, want -1", c, e)
		}
	}
}

func TestEscapeExterior(t *testing.T) {
	// Points outside escape, and further points escape sooner.
	near := escape(complex(0.3, 0.6), 500)
	far := escape(complex(2, 2), 500)
	if near < 0 || far < 0 {
		t.Fatalf("expected both to escape: near=%v far=%v", near, far)
	}
	if far >= near {
		t.Errorf("far point should escape faster: near=%v far=%v", near, far)
	}
}

func TestEscapeSmoothIsContinuous(t *testing.T) {
	// Along a line leaving the set the smooth count should decrease
	// monotonically without integer jumps larger than ~1.
	prev := escape(complex(0.26, 0), 1000)
	for x := 0.27; x < 2.0; x += 0.01 {
		cur := escape(complex(x, 0), 1000)
		if cur < 0 {
			t.Fatalf("point %v unexpectedly inside", x)
		}
		if cur > prev+1e-9 {
			t.Errorf("smooth count increased moving away from set at x=%.2f: %v -> %v", x, prev, cur)
		}
		prev = cur
	}
}

func TestBrailleBitsDistinct(t *testing.T) {
	var seen rune
	for _, row := range brailleBits {
		for _, bit := range row {
			if seen&bit != 0 {
				t.Fatalf("duplicate braille bit %#x", bit)
			}
			seen |= bit
		}
	}
	if seen != 0xFF {
		t.Errorf("braille bits cover %#x, want 0xff", seen)
	}
}

func TestRenderShape(t *testing.T) {
	var buf bytes.Buffer
	w := bufio.NewWriter(&buf)
	cols, rows := 40, 12
	render(w, view{-0.6, 0, 3.2}, cols, rows, 100, false)
	w.Flush()

	lines := strings.Split(strings.TrimRight(buf.String(), "\n"), "\n")
	if len(lines) != rows {
		t.Fatalf("got %d lines, want %d", len(lines), rows)
	}
	for i, ln := range lines {
		if n := utf8.RuneCountInString(ln); n != cols {
			t.Errorf("line %d has %d runes, want %d", i, n, cols)
		}
		for _, r := range ln {
			if r < 0x2800 || r > 0x28FF {
				t.Errorf("line %d has non-braille rune %U", i, r)
			}
		}
	}
	// The center of the default view lands inside the set, so the middle
	// cell should be blank braille (all dots off).
	mid := []rune(lines[rows/2])[cols/2]
	if mid != 0x2800 {
		t.Errorf("center cell %U, want blank braille (inside set)", mid)
	}
}
