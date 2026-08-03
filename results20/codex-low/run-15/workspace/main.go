package main

import (
	"fmt"
	"math/rand"
	"os"
	"os/exec"
	"strings"
	"time"
)

type world struct {
	w, h int
	grid map[int]map[int]bool
}

func newWorld(w, h int) *world {
	return &world{w: w, h: h, grid: make(map[int]map[int]bool)}
}

func (wd *world) live(x, y int) bool {
	if m, ok := wd.grid[x]; ok {
		return m[y]
	}
	return false
}

func (wd *world) set(x, y int, v bool) {
	if _, ok := wd.grid[x]; !ok {
		wd.grid[x] = make(map[int]bool)
	}
	wd.grid[x][y] = v
}

func (wd *world) random(prob float64, rng *rand.Rand) {
	for x := 0; x < wd.w; x++ {
		for y := 0; y < wd.h; y++ {
			if rng.Float64() < prob {
				wd.set(x, y, true)
			}
		}
	}
}

func (wd *world) neighbors(x, y int) int {
	n := 0
	for dx := -1; dx <= 1; dx++ {
		for dy := -1; dy <= 1; dy++ {
			if dx == 0 && dy == 0 {
				continue
			}
			if wd.live(x+dx, y+dy) {
				n++
			}
		}
	}
	return n
}

func (wd *world) step() {
	type cell struct{ x, y int }
	cand := make(map[cell]bool)
	for x, m := range wd.grid {
		for y := range m {
			cand[cell{x, y}] = true
			for dx := -1; dx <= 1; dx++ {
				for dy := -1; dy <= 1; dy++ {
					cand[cell{x + dx, y + dy}] = true
				}
			}
		}
	}
	// Compute next state from the current snapshot, then apply.
	next := make(map[cell]bool)
	for c := range cand {
		n := wd.neighbors(c.x, c.y)
		alive := wd.live(c.x, c.y)
		if alive && (n == 2 || n == 3) {
			next[c] = true
		} else if !alive && n == 3 {
			next[c] = true
		}
	}
	wd.grid = make(map[int]map[int]bool)
	for c := range next {
		wd.set(c.x, c.y, true)
	}
}

func (wd *world) render() string {
	var b strings.Builder
	for y := 0; y < wd.h; y++ {
		for x := 0; x < wd.w; x++ {
			if wd.live(x, y) {
				b.WriteString("\x1b[7m  \x1b[0m")
			} else {
				b.WriteString("  ")
			}
		}
		b.WriteString("\x1b[K\n")
	}
	return b.String()
}

func (wd *world) count() int {
	n := 0
	for _, m := range wd.grid {
		n += len(m)
	}
	return n
}

func (wd *world) glider(x, y int) {
	wd.set(x+1, y, true)
	wd.set(x+2, y+1, true)
	wd.set(x, y+2, true)
	wd.set(x+1, y+2, true)
	wd.set(x+2, y+2, true)
}

func (wd *world) pulsar(x, y int) {
	tri := func(ox, oy int) {
		for i := 1; i <= 2; i++ {
			wd.set(x+ox+i, y+oy, true)
			wd.set(x+ox-i, y+oy, true)
			wd.set(x+ox, y+oy+i, true)
			wd.set(x+ox, y+oy-i, true)
		}
	}
	tri(0, 0)
	tri(0, 5)
	tri(5, 0)
	tri(5, 5)
}

func rawMode()  { exec.Command("stty", "-f", "/dev/stdin", "raw", "-echo").Run() }
func saneMode() { exec.Command("stty", "sane").Run() }

func hideCursor() { fmt.Print("\x1b[?25l") }
func showCursor() { fmt.Print("\x1b[?25h") }
func home()       { fmt.Print("\x1b[H") }

func main() {
	w, h := 60, 30
	stepDelay := 90 * time.Millisecond
	rng := rand.New(rand.NewSource(time.Now().UnixNano()))

	wd := newWorld(w, h)
	wd.glider(w/3, h/2)
	wd.glider(2*w/3-3, h/3)
	wd.pulsar(w/2-4, h/2-4)
	wd.random(0.10, rng)

	rawMode()
	defer saneMode()
	defer showCursor()
	fmt.Print("\x1b[2J")
	hideCursor()

	keys := make(chan rune, 8)
	go func() {
		kb := make([]byte, 1)
		for {
			if _, err := os.Stdin.Read(kb); err != nil {
				return
			}
			keys <- rune(kb[0])
		}
	}()

	gen := 0
	paused := false
	for {
		select {
		case k := <-keys:
			switch k {
			case 'q':
				fmt.Print("\x1b[2J")
				return
			case ' ':
				paused = !paused
			case 's':
				wd.step() // single step while paused
			}
		default:
		}

		home()
		if !paused {
			wd.step()
			gen++
		}
		fmt.Print(wd.render())
		state := "running"
		if paused {
			state = "paused"
		}
		fmt.Printf("\x1b[K generation: %-6d cells: %-4d [%s]  q=quit  space=pause  s=step\n",
			gen, wd.count(), state)

		time.Sleep(stepDelay)
	}
}

func verify() bool {
	// Blinker: horizontal -> vertical
	w2 := newWorld(5, 5)
	w2.set(2, 1, true)
	w2.set(2, 2, true)
	w2.set(2, 3, true)
	w2.step()
	// Should now be vertical at y=2
	if !w2.live(1, 2) || !w2.live(2, 2) || !w2.live(3, 2) {
		return false
	}
	if w2.live(2, 1) || w2.live(2, 3) {
		return false
	}
	return true
}
