package main

import (
	"bufio"
	"fmt"
	"math/rand"
	"os"
	"os/exec"
	"time"
)

type point struct{ x, y int }

const (
	width  = 30
	height = 16
)

type game struct {
	snake  []point
	dir    point
	food   point
	score  int
	level  int
	over   bool
	wait   time.Duration
	screen [][]byte
}

func newGame() *game {
	g := &game{}
	g.reset()
	return g
}

func (g *game) reset() {
	rand.Seed(time.Now().UnixNano())
	g.snake = []point{{width / 2, height / 2}}
	g.dir = point{1, 0}
	g.score = 0
	g.level = 1
	g.over = false
	g.wait = 180 * time.Millisecond
	g.screen = make([][]byte, height)
	for y := range g.screen {
		g.screen[y] = make([]byte, width)
		for x := range g.screen[y] {
			g.screen[y][x] = ' '
		}
	}
	g.placeFood()
}

func (g *game) placeFood() {
	for {
		f := point{rand.Intn(width), rand.Intn(height)}
		collides := false
		for _, s := range g.snake {
			if s == f {
				collides = true
				break
			}
		}
		if !collides {
			g.food = f
			return
		}
	}
}

func (g *game) turnRight() {
	if g.dir.x != -1 {
		g.dir = point{0, 1}
	}
}

func (g *game) turnLeft() {
	if g.dir.x != 1 {
		g.dir = point{0, -1}
	}
}

func (g *game) turnUp() {
	if g.dir.y != 1 {
		g.dir = point{0, -1}
	}
}

func (g *game) turnDown() {
	if g.dir.y != -1 {
		g.dir = point{0, 1}
	}
}

func (g *game) step() {
	head := g.snake[0]
	next := point{head.x + g.dir.x, head.y + g.dir.y}

	// wall collision
	if next.x < 0 || next.x >= width || next.y < 0 || next.y >= height {
		g.over = true
		return
	}

	// food?
	ate := next == g.food

	// self collision (tail moves unless we ate)
	limit := len(g.snake)
	if ate {
		limit--
	}
	for i := 0; i < limit; i++ {
		if g.snake[i] == next {
			g.over = true
			return
		}
	}

	g.snake = append([]point{next}, g.snake...)
	if ate {
		g.score += 10
		g.level = g.score/30 + 1
		g.wait = time.Duration(180-int(20*(g.level-1))) * time.Millisecond
		if g.wait < 70*time.Millisecond {
			g.wait = 70 * time.Millisecond
		}
		g.placeFood()
	} else {
		g.snake = g.snake[:len(g.snake)-1]
	}
}

func (g *game) render(header string) {
	for y := range g.screen {
		for x := range g.screen[y] {
			c := ' '
			for i, s := range g.snake {
				if s.x == x && s.y == y {
					if i == 0 {
						c = '@'
					} else {
						c = 'o'
					}
				}
			}
			if g.food.x == x && g.food.y == y {
				c = '*'
			}
			g.screen[y][x] = byte(c)
		}
	}

	fmt.Print("\033[H")
	fmt.Println(header)
	fmt.Println("+" + repeat("-", width) + "+")
	for y := 0; y < height; y++ {
		fmt.Print("|")
		for x := 0; x < width; x++ {
			fmt.Printf("%c", g.screen[y][x])
		}
		fmt.Println("|")
	}
	fmt.Println("+" + repeat("-", width) + "+")
	fmt.Println("  Score:", g.score, " Level:", g.level, "  [Q]uit  [R]estart")
}

func repeat(s string, n int) string {
	out := make([]byte, n)
	for i := range out {
		out[i] = s[0]
	}
	return string(out)
}

func setupTerminal() *exec.Cmd {
	cmd := exec.Command("stty", "cbreak", "-echo")
	cmd.Stdin = os.Stdin
	_ = cmd.Run()
	cmd2 := exec.Command("stty", "-icanon")
	cmd2.Stdin = os.Stdin
	_ = cmd2.Run()
	return cmd
}

func restoreTerminal() {
	cmd := exec.Command("stty", "sane")
	cmd.Stdin = os.Stdin
	_ = cmd.Run()
	cmd2 := exec.Command("stty", "echo")
	cmd2.Stdin = os.Stdin
	_ = cmd2.Run()
}

func readKey(r *bufio.Reader) (string, bool) {
	b1, err := r.ReadByte()
	if err != nil {
		return "", false
	}
	if b1 == 0x1b {
		b2, err := r.ReadByte()
		if err != nil {
			return "esc", true
		}
		if b2 == '[' {
			b3, err := r.ReadByte()
			if err != nil {
				return "esc", true
			}
			switch b3 {
			case 'A':
				return "up", true
			case 'B':
				return "down", true
			case 'C':
				return "right", true
			case 'D':
				return "left", true
			}
		}
		return "esc", true
	}
	rune := string(b1)
	return rune, true
}

func main() {
	g := newGame()
	fmt.Print("\033[?25l\033[2J")
	defer fmt.Print("\033[?25h\033[0m")
	defer restoreTerminal()
	setupTerminal()
	defer func() {
		if r := recover(); r != nil {
			restoreTerminal()
			fmt.Print("\033[?25h\033[0m\033[2J")
			panic(r)
		}
	}()

	fmt.Println("\n  SNAKE  — arrow keys or WASD to move")
	fmt.Println("  Eat food (*), avoid walls & yourself")
	fmt.Println("  [Q]uit  [R]estart   Press any key to start...")
	fmt.Print("\033[?25h")
	bufio.NewReader(os.Stdin).ReadRune()
	fmt.Print("\033[?25l")

	reader := bufio.NewReader(os.Stdin)
	ticker := time.NewTicker(g.wait)
	input := make(chan string, 8)

	go func() {
		for {
			k, ok := readKey(reader)
			if !ok {
				return
			}
			input <- k
		}
	}()

	g.render("")
	for {
		select {
		case k := <-input:
			switch k {
			case "up", "w":
				g.turnUp()
			case "down", "s":
				g.turnDown()
			case "left", "a":
				g.turnLeft()
			case "right", "d":
				g.turnRight()
			case "q":
				fmt.Print("\033[2J")
				return
			case "r":
				g.reset()
				ticker.Reset(g.wait)
				g.render("")
				continue
			}
		case <-ticker.C:
			if !g.over {
				g.step()
				ticker.Reset(g.wait)
				header := ""
				if g.over {
					header = "  GAME OVER!  Press [R]estart or [Q]uit "
				}
				g.render(header)
			}
		}
	}
}
