# Snake (terminal)

A zero-dependency, single-file terminal version of Snake written in Go.

## Run

```sh
go run .
```

or build and run:

```sh
go build -buildvcs=false -o snake .
./snake
```

## Play

- Move with arrow keys or **WASD**
- Eat `*` food; each gives 10 points
- Avoid the walls and your own tail
- Level up every 30 points — the snake speeds up
- `Q` quit, `R` restart

Requires a terminal that handles ANSI escape sequences (raw mode via `stty`).
