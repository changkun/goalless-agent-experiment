# gol

A tiny, dependency-free Conway's Game of Life simulator written in Go, printed
directly to the terminal.

## Build

```sh
go build -o gol .
```

## Run

```sh
./gol [preset] [-fps N] [-n N] [-list]
```

- `preset` — one of `glider`, `pulsar`, `glider-gun` (default: `glider-gun`)
- `-fps N` — frames per second (default: `10`)
- `-n N`   — stop after N generations; keeps the final frame on screen
- `-list`  — print available presets and exit

## Examples

```sh
./gol glider
./gol pulsar -fps 20
./gol glider-gun -n 100 -fps 5
```

## Tests

```sh
go test ./...
```
