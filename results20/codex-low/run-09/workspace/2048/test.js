"use strict";
const assert = require("assert");
const { slideGrid, Game } = require("./game");

function eq(actual, expected, msg) {
  assert.deepStrictEqual(actual, expected, msg);
}

// Slide right merging
const g1 = [
  [2, 2, 0, 0],
  [2, 2, 4, 4],
  [0, 0, 0, 0],
  [2, 4, 8, 16],
];
const r1 = slideGrid(g1, "right");
eq(r1.grid[0], [0, 0, 0, 4], "slide right simple");
eq(r1.score, 16, "score from 2+2 and 2+2+4+4");
assert.ok(r1.changed, "should have changed");

// Slide left
const g2 = [
  [0, 0, 0, 4],
  [0, 0, 0, 0],
  [0, 0, 0, 0],
  [0, 0, 0, 0],
];
const r2 = slideGrid(g2, "left");
eq(r2.grid[0], [4, 0, 0, 0], "slide left");

// Slide up
const g3 = [
  [0, 2, 0, 0],
  [0, 2, 0, 0],
  [0, 4, 0, 0],
  [0, 0, 0, 0],
];
const r3 = slideGrid(g3, "up");
eq(r3.grid[0], [0, 4, 0, 0], "slide up merge");
eq(r3.grid[1], [0, 4, 0, 0], "slide up second row");
eq(r3.score, 4, "up score");

// Slide down
const r4 = slideGrid(g3, "down");
eq(r4.grid[3], [0, 4, 0, 0], "slide down merge");
eq(r4.grid[2], [0, 4, 0, 0], "slide down second row");
eq(r4.score, 4, "down score");

// No change when blocked
const blocked = [
  [2, 4, 8, 16],
  [4, 8, 16, 32],
  [8, 16, 32, 64],
  [16, 32, 64, 128],
];
const rb = slideGrid(blocked, "left");
assert.strictEqual(rb.changed, false, "no move should not change");

// Game: move + undo roundtrip
const game = new Game();
const before = game.grid.map((r) => r.slice());
const beforeScore = game.score;
game.move("left");
const afterMove = game.grid.map((r) => r.slice());
game.undo();
eq(game.grid, before, "undo restores grid");
eq(game.score, beforeScore, "undo restores score");
eq(game.history.length, 0, "undo clears history");

// addTile fills all cells
function countTiles(g) {
  return g.flat().filter((v) => v !== 0).length;
}
assert.strictEqual(countTiles(new Game().grid), 2, "starts with two tiles");

console.log("All 2048 logic tests passed ✅");
