package main

import (
	"sort"
	"testing"
)

type cell struct{ x, y int }

func liveCells(g *Grid) []cell {
	var out []cell
	for y := 0; y < g.H; y++ {
		for x := 0; x < g.W; x++ {
			if g.Cells[y][x] {
				out = append(out, cell{x, y})
			}
		}
	}
	sort.Slice(out, func(i, j int) bool {
		if out[i].y != out[j].y {
			return out[i].y < out[j].y
		}
		return out[i].x < out[j].x
	})
	return out
}

func TestGliderTranslatesAfterFourSteps(t *testing.T) {
	g := NewGrid(16, 16)
	// Canonical glider, anchored top-left.
	g.LoadPattern(1, 1, `.O.
..O
OOO`)
	start := liveCells(g)
	for i := 0; i < 4; i++ {
		g.Step()
	}
	after := liveCells(g)
	if len(start) != len(after) {
		t.Fatalf("glider changed cell count: %d -> %d", len(start), len(after))
	}
	// The glider is a period-4 oscillator in its own frame: after 4 steps
	// the shape is identical but translated. Verify relative offsets match.
	ox, oy := after[0].x-start[0].x, after[0].y-start[0].y
	for i := range start {
		rel := cell{start[i].x - start[0].x, start[i].y - start[0].y}
		want := cell{after[i].x - (start[0].x + ox), after[i].y - (start[0].y + oy)}
		if rel != want {
			t.Fatalf("shape changed after 4 steps: rel=%+v want=%+v", rel, want)
		}
	}
}

func TestBlinker(t *testing.T) {
	g := NewGrid(5, 5)
	g.LoadPattern(1, 1, `OOO`)
	g.Step()
	got := liveCells(g)
	exp := []cell{{2, 0}, {2, 1}, {2, 2}}
	if len(got) != len(exp) {
		t.Fatalf("blinker brain: got %v want %v", got, exp)
	}
	for i, c := range got {
		if c != exp[i] {
			t.Fatalf("blinker: got %v want %v", got, exp)
		}
	}
}

func TestStillLifeBlock(t *testing.T) {
	g := NewGrid(5, 5)
	g.LoadPattern(1, 1, `OO
OO`)
	before := liveCells(g)
	g.Step()
	after := liveCells(g)
	if len(before) != 4 || len(after) != 4 {
		t.Fatalf("block died: before %v after %v", before, after)
	}
	for i := range before {
		if before[i] != after[i] {
			t.Fatalf("block not static: before %v after %v", before, after)
		}
	}
}
