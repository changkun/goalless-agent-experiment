package main

import "testing"

func TestBlinker(t *testing.T) {
	wd := newWorld(5, 5)
	wd.set(2, 1, true)
	wd.set(2, 2, true)
	wd.set(2, 3, true)
	wd.step()
	if !wd.live(1, 2) || !wd.live(2, 2) || !wd.live(3, 2) {
		t.Fatalf("expected vertical blinker, got horizontal persistence")
	}
	if wd.live(2, 1) || wd.live(2, 3) {
		t.Fatalf("expected horizontal cells to die")
	}
}

func TestStillLife(t *testing.T) {
	wd := newWorld(4, 4)
	// 2x2 block is a still life
	for x := 1; x <= 2; x++ {
		for y := 1; y <= 2; y++ {
			wd.set(x, y, true)
		}
	}
	wd.step()
	if wd.count() != 4 {
		t.Fatalf("block changed size: %d", wd.count())
	}
	for x := 1; x <= 2; x++ {
		for y := 1; y <= 2; y++ {
			if !wd.live(x, y) {
				t.Fatalf("block cell (%d,%d) died", x, y)
			}
		}
	}
}
