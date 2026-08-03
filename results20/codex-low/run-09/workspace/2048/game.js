"use strict";

const readline = require("readline");

const SIZE = 4;

function blankGrid() {
  return Array.from({ length: SIZE }, () => Array(SIZE).fill(0));
}

function gridEquals(a, b) {
  for (let r = 0; r < SIZE; r++)
    for (let c = 0; c < SIZE; c++)
      if (a[r][c] !== b[r][c]) return false;
  return true;
}

function cloneGrid(g) {
  return g.map((row) => row.slice());
}

function emptyCells(g) {
  const cells = [];
  for (let r = 0; r < SIZE; r++)
    for (let c = 0; c < SIZE; c++) if (g[r][c] === 0) cells.push([r, c]);
  return cells;
}

function addTile(g) {
  const cells = emptyCells(g);
  if (!cells.length) return;
  const [r, c] = cells[Math.floor(Math.random() * cells.length)];
  g[r][c] = Math.random() < 0.9 ? 2 : 4;
}

// Compress a single line left and merge, returning [newLine, gainedScore]
function slideLine(line) {
  const kept = line.filter((v) => v !== 0);
  const out = [];
  let score = 0;
  for (let i = 0; i < kept.length; i++) {
    if (kept[i] === kept[i + 1]) {
      out.push(kept[i] * 2);
      score += kept[i] * 2;
      i++;
    } else {
      out.push(kept[i]);
    }
  }
  while (out.length < SIZE) out.push(0);
  return [out, score];
}

function slideGrid(g, dir) {
  let rotated = cloneGrid(g);
  const turns = { left: 0, up: 3, right: 2, down: 1 }[dir];
  for (let i = 0; i < turns; i++) rotated = rotateCW(rotated);

  let score = 0;
  let moved = rotated.map((row) => {
    const [newRow, gained] = slideLine(row);
    score += gained;
    return newRow;
  });

  for (let i = 0; i < (4 - turns) % 4; i++) moved = rotateCW(moved);
  return { grid: moved, score, changed: !gridEquals(moved, g) };
}

function rotateCW(g) {
  const out = blankGrid();
  for (let r = 0; r < SIZE; r++)
    for (let c = 0; c < SIZE; c++) out[c][SIZE - 1 - r] = g[r][c];
  return out;
}

function anyMovesLeft(g) {
  if (emptyCells(g).length) return true;
  for (let r = 0; r < SIZE; r++)
    for (let c = 0; c < SIZE; c++) {
      if (c + 1 < SIZE && g[r][c] === g[r][c + 1]) return true;
      if (r + 1 < SIZE && g[r][c] === g[r + 1][c]) return true;
    }
  return false;
}

function maxTile(g) {
  return Math.max(...g.map((row) => Math.max(...row)));
}

class Game {
  constructor() {
    this.grid = blankGrid();
    this.score = 0;
    this.best = 0;
    this.won = false;
    this.over = false;
    this.finished = false;
    this.history = [];
    addTile(this.grid);
    addTile(this.grid);
  }

  move(dir) {
    if (this.finished) return;
    this.history.push({
      grid: cloneGrid(this.grid),
      score: this.score,
      won: this.won,
    });
    const { grid, score, changed } = slideGrid(this.grid, dir);
    if (changed) {
      this.grid = grid;
      this.score += score;
      addTile(this.grid);
    } else {
      this.history.pop();
      return;
    }
    if (this.history.length > 64) this.history.shift();

    if (maxTile(this.grid) >= 2048 && !this.won) this.won = true;
    if (!anyMovesLeft(this.grid)) {
      this.over = true;
      this.finished = true;
    }
  }

  undo() {
    if (!this.history.length || this.finished) return;
    const prev = this.history.pop();
    this.grid = prev.grid;
    this.score = prev.score;
    this.won = prev.won;
    this.over = false;
    this.finished = false;
  }

  reset() {
    this.best = Math.max(this.best, this.score);
    this.grid = blankGrid();
    this.score = 0;
    this.won = false;
    this.over = false;
    this.finished = false;
    this.history = [];
    addTile(this.grid);
    addTile(this.grid);
  }
}

const COLORS = [
  0,
  "\x1b[97;48;5;236m", // 2
  "\x1b[97;48;5;238m", // 4
  "\x1b[97;48;5;3m", // 8
  "\x1b[97;48;5;202m", // 16
  "\x1b[97;48;5;196m", // 32
  "\x1b[97;48;5;124m", // 64
  "\x1b[97;48;5;220m", // 128
  "\x1b[97;48;5;214m", // 256
  "\x1b[97;48;5;208m", // 512
  "\x1b[1;97;48;5;202m", // 1024
  "\x1b[1;97;48;5;196m", // 2048
];

function colorIndex(value) {
  return Math.min(Math.log2(value), COLORS.length - 1);
}

function render(g) {
  const dash = "      ";
  const top = "\x1b[2m  " + (dash + "+").repeat(SIZE) + "\x1b[0m\n";
  let out = top;
  for (const row of g) {
    out += "\x1b[2m  +" + "------+".repeat(SIZE) + "\x1b[0m\n";
    for (const v of row) {
      const label = v === 0 ? "  " : String(v).padStart(4, " ");
      const cell =
        v === 0 ? `  ${label}  ` : ` ${COLORS[colorIndex(v)]}${label} \x1b[0m`;
      out += `   \x1b[2m|\x1b[0m${cell}`;
    }
    out += `  \x1b[2m|\x1b[0m\n`;
    out += "\x1b[2m  +" + "------+".repeat(SIZE) + "\x1b[0m\n";
  }
  return out;
}

const HINTS = [
  "Arrows/WASD  move",
  "U  undo",
  "R  restart",
  "Q  quit",
];

function draw(game, status) {
  const title = "\x1b[1;36m  2048\x1b[0m";
  const score = `Score: ${game.score}  Best: ${Math.max(game.best, game.score)}`;
  const line = "\x1b[2m  " + "=".repeat(30) + "\x1b[0m";
  let out = "\x1b[?25l\x1b[H\x1b[2J" + title + "\n\n";
  out += `  ${score}\n\n`;
  out += render(game.grid);
  if (status) out += "\n  " + status + "\n";
  out += "\n\x1b[2m  " + HINTS.join("   ") + "\x1b[0m\n";
  process.stdout.write(out);
}

function main() {
  const game = new Game();
  const keys = new Map([
    ["\x1b[A", "up"], ["w", "up"], ["W", "up"],
    ["\x1b[B", "down"], ["s", "down"], ["S", "down"],
    ["\x1b[C", "right"], ["d", "right"], ["D", "right"],
    ["\x1b[D", "left"], ["a", "left"], ["A", "left"],
  ]);

  readline.emitKeypressEvents(process.stdin);
  if (process.stdin.isTTY) process.stdin.setRawMode(true);
  process.stdin.resume();

  draw(game);

  process.stdin.on("keypress", (str, key) => {
    if (key && key.name === "q") return cleanup(0);
    if (key && key.name === "r") {
      game.reset();
      return draw(game);
    }
    if (key && key.name === "u") {
      const status = game.history.length ? "Undid last move" : "Nothing to undo";
      game.undo();
      return draw(game, status);
    }
    const dir = keys.get(str);
    if (dir) {
      game.move(dir);
      let status = "";
      if (game.over) status = "\x1b[1;31mGame over.\x1b[0m";
      else if (game.won && !game.finished)
        status = "\x1b[1;32mYou reached 2048! Keep going or restart.\x1b[0m";
      return draw(game, status);
    }
    if (key && key.name === "c") return cleanup(0);
  });

  function cleanup(code) {
    process.stdin.setRawMode(false);
    process.stdin.pause();
    process.stdout.write("\x1b[?25h");
    process.exit(code);
  }
}

if (require.main === module) main();

module.exports = { Game, slideGrid, render, blankGrid };
