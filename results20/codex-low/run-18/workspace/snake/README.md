# Terminal Snake

A classic Snake game that runs right in your terminal, written in Go with zero dependencies.

## Run

```sh
go run .
```

Or build a binary:

```sh
go build -buildvcs=false -o snake .
./snake
```

## Controls

- **Arrows** or **WASD** (also `hjkl`) — move
- **r** — restart after game over
- **q** — quit

Eat the `*`, avoid the walls and yourself. The head is `@`, body is `o`.

## Notes

- Uses raw mode via `ioctl`/`syscall` directly, so no external packages are needed.
- Only the game loop ticks; input is read non-blockingly between frames.
