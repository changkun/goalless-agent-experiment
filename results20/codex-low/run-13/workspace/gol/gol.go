package main

import (
	"bytes"
	"fmt"
	"os"
	"os/exec"
	"strings"
	"time"
)

// Grid holds the cellular automaton state.
type Grid struct {
	W, H  int
	Cells [][]bool
}

// NewGrid creates a blank grid of the given size.
func NewGrid(w, h int) *Grid {
	cells := make([][]bool, h)
	for i := range cells {
		cells[i] = make([]bool, w)
	}
	return &Grid{W: w, H: h, Cells: cells}
}

// Set flips a cell on at (x, y), ignoring out-of-bounds coordinates.
func (g *Grid) Set(x, y int) {
	if x < 0 || y < 0 || x >= g.W || y >= g.H {
		return
	}
	g.Cells[y][x] = true
}

// Neighbors counts live neighbors of (x, y).
func (g *Grid) Neighbors(x, y int) int {
	n := 0
	for dy := -1; dy <= 1; dy++ {
		for dx := -1; dx <= 1; dx++ {
			if dx == 0 && dy == 0 {
				continue
			}
			nx, ny := x+dx, y+dy
			if nx < 0 || ny < 0 || nx >= g.W || ny >= g.H {
				continue
			}
			if g.Cells[ny][nx] {
				n++
			}
		}
	}
	return n
}

// Step advances the simulation by one generation.
func (g *Grid) Step() {
	next := make([][]bool, g.H)
	for y := range next {
		next[y] = make([]bool, g.W)
		for x := range next[y] {
			n := g.Neighbors(x, y)
			if g.Cells[y][x] {
				next[y][x] = n == 2 || n == 3 // survival
			} else {
				next[y][x] = n == 3 // birth
			}
		}
	}
	g.Cells = next
}

// Alive counts the number of live cells.
func (g *Grid) Alive() int {
	n := 0
	for _, row := range g.Cells {
		for _, c := range row {
			if c {
				n++
			}
		}
	}
	return n
}

// Render returns the grid as a string of '#' (live) and '.' (dead).
func (g *Grid) Render() string {
	var b bytes.Buffer
	for _, row := range g.Cells {
		for _, c := range row {
			if c {
				b.WriteByte('#')
			} else {
				b.WriteByte('.')
			}
		}
		b.WriteByte('\n')
	}
	return b.String()
}

// LoadPattern blits a fromString pattern anchored at (x, y).
func (g *Grid) LoadPattern(x, y int, pattern string) {
	rows := strings.Split(strings.TrimRight(pattern, "\n"), "\n")
	for py, row := range rows {
		for px, ch := range row {
			if ch == 'O' || ch == '#' {
				g.Set(x+px, y+py)
			}
		}
	}
}

// clearScreen moves the cursor home and clears the terminal.
func clearScreen() {
	fmt.Print("\x1b[2J\x1b[H")
}

// hideCursor and showCursor control terminal cursor visibility.
func hideCursor() { fmt.Print("\x1b[?25l") }
func showCursor() { fmt.Print("\x1b[?25h") }

func main() {
	presets := map[string]struct {
		Pattern string
		W, H    int
	}{
		"glider": {
			W: 32, H: 16,
			Pattern: `....O
O..O.
.OOO.`,
		},
		"pulsar": {
			W: 40, H: 40,
			Pattern: `..OOO...OOO..
..............
O....O.O....O
O....O.O....O
O....O.O....O
..OOO...OOO..
..............
..OOO...OOO..
O....O.O....O
O....O.O....O
O....O.O....O
..............
..OOO...OOO..`,
		},
		"glider-gun": {
			W: 80, H: 24,
			Pattern: `........................O...........
......................O.O...........
............OO......OO............OO
...........O...O....OO............OO
OO........O.....O...OO..............
OO........O...O.OO....O.O...........
..........O.....O.......O...........
...........O...O....................
............OO......................`,
		},
	}

	name := "glider-gun"
	fps := 10
	genLimit := 0
	for i := 1; i < len(os.Args); i++ {
		arg := os.Args[i]
		switch {
		case arg == "-list":
			keys := []string{"glider", "pulsar", "glider-gun"}
			fmt.Println("presets:", strings.Join(keys, ", "))
			return
		case arg == "-fps" && i+1 < len(os.Args):
			if _, err := fmt.Sscanf(os.Args[i+1], "%d", &fps); err == nil {
				i++
			}
		case arg == "-n" && i+1 < len(os.Args):
			if _, err := fmt.Sscanf(os.Args[i+1], "%d", &genLimit); err == nil {
				i++
			}
		case arg[0] != '-':
			name = arg
		}
	}

	p, ok := presets[name]
	if !ok {
		fmt.Fprintf(os.Stderr, "unknown preset %q (try -list)\n", name)
		os.Exit(1)
	}

	g := NewGrid(p.W, p.H)
	// Center the pattern on the grid.
	rows := strings.Split(strings.TrimRight(p.Pattern, "\n"), "\n")
	g.LoadPattern((p.W-len(rows[0]))/2, (p.H-len(rows))/2, p.Pattern)

	interval := time.Second / time.Duration(fps)
	hideCursor()
	clearScreen()
	defer showCursor()

	gen := 0
	for {
		if genLimit > 0 && gen >= genLimit {
			break
		}
		clearScreen()
		fmt.Printf("preset=%s gen=%d alive=%d\n\n", name, gen, g.Alive())
		fmt.Print(g.Render())
		g.Step()
		gen++
		time.Sleep(interval)
	}

	// Keep the final frame visible when a generation limit is set.
	if genLimit > 0 {
		fmt.Print("\n\n(press any key to exit)")
		exec.Command("stty", "cbreak", "-echo").Run()
		var b [1]byte
		os.Stdin.Read(b[:])
		exec.Command("stty", "-cbreak", "echo").Run()
	}
}
