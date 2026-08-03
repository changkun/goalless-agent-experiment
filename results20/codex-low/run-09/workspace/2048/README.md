# 2048

A dependency-free, terminal-based [2048](https://en.wikipedia.org/wiki/2048_(video_game))
game written in Node.js.

## Run

```sh
npm start
# or
node game.js
```

## Play

| Key              | Action      |
| ---------------- | ----------- |
| `← → ↑ ↓` / WASD | Move tiles  |
| `u`              | Undo (64 moves) |
| `r`              | Restart     |
| `q` / `Ctrl+C`   | Quit        |

## Test

```sh
node test.js
```

The game logic (`slideGrid`, `Game`) is exposed as a module and verified by the
test suite in `test.js`.
