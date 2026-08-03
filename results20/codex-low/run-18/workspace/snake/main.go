package main

import (
	"fmt"
	"math/rand"
	"os"
	"syscall"
	"time"
	"unsafe"
)

const (
	width  = 40
	height = 20
)

type point struct{ x, y int }

type game struct {
	snake    []point
	dir      point
	nextDir  point
	food     point
	score    int
	gameOver bool
	grid     [height][width]byte
}

func newGame() *game {
	g := &game{}
	g.reset()
	return g
}

func (g *game) reset() {
	g.snake = []point{{width / 2, height / 2}}
	g.dir = point{1, 0}
	g.nextDir = g.dir
	g.score = 0
	g.gameOver = false
	g.placeFood()
}

func (g *game) placeFood() {
	for {
		p := point{rand.Intn(width), rand.Intn(height)}
		occupied := false
		for _, s := range g.snake {
			if s == p {
				occupied = true
				break
			}
		}
		if !occupied {
			g.food = p
			return
		}
	}
}

func (g *game) step() {
	if !(g.nextDir.x == -g.dir.x && g.nextDir.y == -g.dir.y) {
		g.dir = g.nextDir
	}

	head := g.snake[0]
	newHead := point{head.x + g.dir.x, head.y + g.dir.y}

	if newHead.x < 0 || newHead.x >= width || newHead.y < 0 || newHead.y >= height {
		g.gameOver = true
		return
	}

	growing := newHead == g.food

	body := g.snake
	if !growing {
		body = g.snake[:len(g.snake)-1]
	}
	for _, s := range body {
		if s == newHead {
			g.gameOver = true
			return
		}
	}

	g.snake = append([]point{newHead}, g.snake...)
	if growing {
		g.score++
		g.placeFood()
	} else {
		g.snake = g.snake[:len(g.snake)-1]
	}
}

func (g *game) render() {
	for y := 0; y < height; y++ {
		for x := 0; x < width; x++ {
			g.grid[y][x] = ' '
		}
	}
	for _, s := range g.snake {
		g.grid[s.y][s.x] = 'o'
	}
	g.grid[g.snake[0].y][g.snake[0].x] = '@'
	g.grid[g.food.y][g.food.x] = '*'

	// cursor home and clear
	fmt.Print("\x1b[H\x1b[2J")
	fmt.Printf("  SNAKE   score: %d\n", g.score)
	fmt.Print("  +")
	for x := 0; x < width; x++ {
		fmt.Print("-")
	}
	fmt.Println("+")

	for y := 0; y < height; y++ {
		fmt.Print("  |")
		for x := 0; x < width; x++ {
			fmt.Printf("%c", g.grid[y][x])
		}
		fmt.Println("|")
	}

	fmt.Print("  +")
	for x := 0; x < width; x++ {
		fmt.Print("-")
	}
	fmt.Println("+")

	if g.gameOver {
		fmt.Printf("  GAME OVER - final score: %d\n", g.score)
		fmt.Println("  press 'r' to restart, 'q' to quit")
	} else {
		fmt.Println("  arrows/wasd move | q quit | r restart")
	}
}

// makeRaw puts the terminal into raw mode on Linux without external deps.
func makeRaw(fd int) (func(), error) {
	var termios syscall.Termios
	if _, _, errno := syscall.Syscall(syscall.SYS_IOCTL, uintptr(fd),
		uintptr(syscall.TCGETS), uintptr(unsafe.Pointer(&termios))); errno != 0 {
		return nil, errno
	}
	old := termios

	termios.Iflag &^= syscall.IGNBRK | syscall.BRKINT | syscall.PARMRK | syscall.ISTRIP |
		syscall.INLCR | syscall.IGNCR | syscall.ICRNL | syscall.IXON
	termios.Lflag &^= syscall.ECHO | syscall.ECHONL | syscall.ICANON | syscall.ISIG | syscall.IEXTEN
	termios.Cflag &^= syscall.CSIZE | syscall.PARENB
	termios.Cflag |= syscall.CS8
	termios.Cc[syscall.VMIN] = 1
	termios.Cc[syscall.VTIME] = 0

	if _, _, errno := syscall.Syscall(syscall.SYS_IOCTL, uintptr(fd),
		uintptr(syscall.TCSETS), uintptr(unsafe.Pointer(&termios))); errno != 0 {
		return nil, errno
	}

	return func() {
		syscall.Syscall(syscall.SYS_IOCTL, uintptr(fd),
			uintptr(syscall.TCSETS), uintptr(unsafe.Pointer(&old)))
	}, nil
}

func main() {
	restore, err := makeRaw(int(os.Stdin.Fd()))
	if err != nil {
		fmt.Fprintln(os.Stderr, "error entering raw mode:", err)
		return
	}
	defer restore()
	defer fmt.Print("\x1b[?25h\x1b[0m\n") // show cursor + reset

	rand.Seed(time.Now().UnixNano())
	g := newGame()
	g.render()

	input := make(chan byte, 1)
	go func() {
		buf := make([]byte, 1)
		for {
			n, err := os.Stdin.Read(buf)
			if err != nil || n == 0 {
				close(input)
				return
			}
			select {
			case input <- buf[0]:
			default:
			}
		}
	}()

	ticker := time.NewTicker(80 * time.Millisecond)
	defer ticker.Stop()

	for {
		select {
		case b, ok := <-input:
			if !ok {
				return
			}
			switch b {
			case 'q':
				return
			case 'r':
				g.reset()
				g.render()
			case 'w', 'W', 'k':
				g.nextDir = point{0, -1}
			case 's', 'S', 'j':
				g.nextDir = point{0, 1}
			case 'a', 'A', 'h':
				g.nextDir = point{-1, 0}
			case 'd', 'D', 'l':
				g.nextDir = point{1, 0}
			case 27: // escape: arrow keys
				seq := make([]byte, 2)
				if _, err := os.Stdin.Read(seq); err != nil {
					continue
				}
				if seq[0] == '[' {
					switch seq[1] {
					case 'A':
						g.nextDir = point{0, -1}
					case 'B':
						g.nextDir = point{0, 1}
					case 'C':
						g.nextDir = point{1, 0}
					case 'D':
						g.nextDir = point{-1, 0}
					}
				}
			}
			if !g.gameOver {
				g.render()
			}
		case <-ticker.C:
			if !g.gameOver {
				g.step()
				g.render()
			}
		}
	}
}
