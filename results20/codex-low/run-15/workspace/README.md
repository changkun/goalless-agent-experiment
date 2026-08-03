# Terminal Game of Life

A Conway's Game of Life that runs directly in your terminal, written in Go.

## Features

- Animated cellular automaton with ANSI block rendering
- Keyboard controls: pause/resume, single-step, quit
- Mixed initial patterns: gliders, a pulsar, and random noise
- Infinite grid (cells live in a sparse map) — no fixed boundary
- Zero external dependencies

## Usage

```sh
go run .
```

Or build a binary:

```sh
go build -o golife .
./golife
```

### Controls

| Key    | Action                    |
|--------|---------------------------|
| `q`    | Quit                      |
| `space`| Pause / resume           |
| `s`    | Single-step (while paused)|

## How it works

Each generation is computed by considering every live cell and its
neighboring cells, applying the classic rules (birth on 3 neighbors,
survival on 2 or 3, death otherwise). The world is stored as a sparse
map, so patterns can drift off-screen freely without boundary artifacts.

## Tests

```sh
go test ./...
```
