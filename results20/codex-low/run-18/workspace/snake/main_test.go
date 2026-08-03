package main

import "testing"

func TestSnakeGrowsAndScores(t *testing.T) {
	g := newGame()
	g.reset()
	// Force food directly in front of the head
	head := g.snake[0]
	g.food = point{head.x + 1, head.y}
	g.dir = point{1, 0}
	g.nextDir = g.dir
	lengthBefore := len(g.snake)
	g.step()
	if g.gameOver {
		t.Fatal("expected not game over")
	}
	if len(g.snake) != lengthBefore+1 {
		t.Fatalf("expected snake to grow, got %d -> %d", lengthBefore, len(g.snake))
	}
	if g.score != 1 {
		t.Fatalf("expected score 1, got %d", g.score)
	}
}

func TestSelfCollision(t *testing.T) {
	g := newGame()
	g.reset()
	// Build a snake loop that will hit itself
	g.snake = []point{
		{5, 5}, {6, 5}, {7, 5}, {7, 6}, {6, 6},
	}
	g.dir = point{1, 0}
	g.nextDir = point{1, 0}
	g.food = point{0, 0} // not eaten, tail moves away
	g.step()
	if !g.gameOver {
		t.Fatal("expected game over from self collision")
	}
}

func TestWallCollision(t *testing.T) {
	g := newGame()
	g.reset()
	g.snake = []point{{width - 1, 5}}
	g.dir = point{1, 0}
	g.nextDir = point{1, 0}
	g.food = point{0, 0}
	g.step()
	if !g.gameOver {
		t.Fatal("expected game over from wall")
	}
}

func TestCannotReverse(t *testing.T) {
	g := newGame()
	g.reset()
	g.dir = point{1, 0}
	g.nextDir = point{-1, 0} // reverse into itself
	g.food = point{100, 100} // place food far away (won't be eaten)
	// To avoid acting as food, offset it beyond the grid
	g.food = point{0, 0}
	g.step()
	if g.dir.x == -1 {
		t.Fatal("direction should not reverse")
	}
}
