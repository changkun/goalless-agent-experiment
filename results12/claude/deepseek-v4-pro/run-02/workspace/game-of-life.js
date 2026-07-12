#!/usr/bin/env node

/*
 *  ╔══════════════════════════════════════════════╗
 *  ║     Conway's Game of Life — Terminal Edition ║
 *  ╚══════════════════════════════════════════════╝
 *
 *  Controls:
 *    Space / P      Play/Pause
 *    R              Randomise the board
 *    C              Clear the board
 *    +/-            Speed up / slow down
 *    Arrow keys     Move cursor
 *    Enter / Click  Toggle cell at cursor
 *    1-7            Load pattern preset
 *    Q / Esc        Quit
 *
 *  Presets:
 *    1  Glider              5  Pulsar
 *    2  Lightweight SS      6  Diehard
 *    3  Glider Gun          7  Pentadecathlon
 *    4  R-pentomino
 */

const { stdout, stdin } = process;

// ─── Configuration ───────────────────────────────────────────────────────────

const CFG = {
  tickInterval: 80, // ms between generations
  minInterval: 10,
  maxInterval: 500,
  boardRows: 0, // set after terminal size detection
  boardCols: 0,
  cellChar: '█',
  deadChar: '·',
  cursorStyle: 'inverse',
  aliveColor: '\x1b[38;5;82m', // bright green
  deadColor: '\x1b[38;5;240m',  // dark gray
  cursorColor: '\x1b[48;5;240m',
  reset: '\x1b[0m',
  statsColor: '\x1b[38;5;39m',  // cyan
  titleColor: '\x1b[38;5;226m', // yellow
  borderColor: '\x1b[38;5;99m', // purple
  helpColor: '\x1b[38;5;245m',  // medium gray
};

// ─── State ───────────────────────────────────────────────────────────────────

let board = [];
let nextBoard = [];
let running = false;
let generation = 0;
let cursorX = 0;
let cursorY = 0;
let tickTimer = null;
let cols = 0;
let rows = 0;

// ─── Terminal Setup ──────────────────────────────────────────────────────────

function setup() {
  const tsize = stdout.getWindowSize ? stdout.getWindowSize() : [80, 24];
  cols = Math.max(20, Math.floor((tsize[0] - 2) / 2)); // 2 chars per cell (cell+space) + border
  rows = Math.max(10, tsize[1] - 8); // room for title bar, status bar, help

  CFG.boardCols = cols;
  CFG.boardRows = rows;

  board = Array.from({ length: rows }, () => new Uint8Array(cols));
  nextBoard = Array.from({ length: rows }, () => new Uint8Array(cols));

  cursorX = Math.floor(cols / 2);
  cursorY = Math.floor(rows / 2);

  stdout.write('\x1b[?25l');        // hide cursor
  stdout.write('\x1b[?1000h');      // enable mouse tracking
  stdout.write('\x1b[?1006h');      // sgr extended mouse mode
  stdout.write('\x1b[?1049h');      // switch to alternate screen buffer
  stdout.write('\x1b[2J');          // clear

  if (stdin.setRawMode) stdin.setRawMode(true);
  stdin.resume();
  stdin.setEncoding('utf8');

  stdin.on('data', handleInput);
  process.on('exit', cleanup);
  process.on('SIGINT', () => { cleanup(); process.exit(); });
  process.on('SIGTERM', () => { cleanup(); process.exit(); });

  // Handle terminal resize
  stdout.on('resize', () => {
    const nsize = stdout.getWindowSize();
    const ncols = Math.max(20, Math.floor((nsize[0] - 2) / 2));
    const nrows = Math.max(10, nsize[1] - 8);
    if (ncols !== cols || nrows !== rows) {
      cols = ncols; rows = nrows;
      CFG.boardCols = cols; CFG.boardRows = rows;
      const oldB = board, oldN = nextBoard;
      board = Array.from({ length: rows }, (_, y) => {
        const r = new Uint8Array(cols);
        if (y < oldB.length) {
          for (let x = 0; x < Math.min(cols, oldB[y].length); x++) r[x] = oldB[y][x];
        }
        return r;
      });
      nextBoard = Array.from({ length: rows }, () => new Uint8Array(cols));
      cursorX = Math.min(cursorX, cols - 1);
      cursorY = Math.min(cursorY, rows - 1);
    }
  });
}

function cleanup() {
  if (tickTimer) clearInterval(tickTimer);
  stdout.write('\x1b[?25h');         // show cursor
  stdout.write('\x1b[?1000l');       // disable mouse
  stdout.write('\x1b[?1006l');
  stdout.write('\x1b[?1049l');       // restore screen buffer
  stdout.write('\x1b[0m');           // reset colors
  if (stdin.setRawMode) stdin.setRawMode(false);
}

// ─── Input Handling ──────────────────────────────────────────────────────────

let escapeBuffer = '';

function handleInput(data) {
  const ch = data.toString();

  // Mouse events (SGR extended mode: \x1b[<Cb;Cx;Cy[Mm])
  if (ch.startsWith('\x1b[<')) {
    const match = ch.match(/\x1b\[<(\d+);(\d+);(\d+)([Mm])/);
    if (match) {
      const [, btn, mx, my, action] = match;
      const clickX = Math.floor((parseInt(mx) - 1) / 2);
      const clickY = parseInt(my) - 3; // title + header offset
      if (clickY >= 0 && clickY < rows && clickX >= 0 && clickX < cols) {
        if (btn === '0' && action === 'M') { // Left button down
          board[clickY][clickX] = board[clickY][clickX] ? 0 : 1;
          generation = 0;
          cursorX = clickX; cursorY = clickY;
          render();
        }
        if (btn === '32' || btn === '64') { // Motion with button held
          board[clickY][clickX] = 1;
          cursorX = clickX; cursorY = clickY;
          render();
        }
      }
    }
    return;
  }

  // Escape sequences
  if (ch === '\x1b') { escapeBuffer = '\x1b'; return; }
  if (escapeBuffer) {
    escapeBuffer += ch;
    if (escapeBuffer === '\x1b[A') { cursorY = Math.max(0, cursorY - 1); render(); }
    else if (escapeBuffer === '\x1b[B') { cursorY = Math.min(rows - 1, cursorY + 1); render(); }
    else if (escapeBuffer === '\x1b[C') { cursorX = Math.min(cols - 1, cursorX + 1); render(); }
    else if (escapeBuffer === '\x1b[D') { cursorX = Math.max(0, cursorX - 1); render(); }
    else if (escapeBuffer.length >= 5 && escapeBuffer.startsWith('\x1b[')) {
      if (ch === 'R' || ch === '~' || (ch >= '0' && ch <= '9') || ch === ';') return; // keep buffering
    }
    if (!/^\x1b\[[\d;]*[A-Za-z~]?$/.test(escapeBuffer)) escapeBuffer = ''; // unrecognised, reset
    else if (/^\x1b\[[\d;]*[A-Za-z~]$/.test(escapeBuffer)) escapeBuffer = ''; // complete
    return;
  }

  switch (ch) {
    case ' ':
    case 'p':
      if (running) pause(); else play();
      break;
    case 'r':
      randomise();
      generation = 0;
      render();
      break;
    case 'c':
      clearBoard();
      generation = 0;
      render();
      break;
    case '+':
    case '=':
      CFG.tickInterval = Math.max(CFG.minInterval, CFG.tickInterval - 15);
      if (running) { pause(); play(); }
      render();
      break;
    case '-':
      CFG.tickInterval = Math.min(CFG.maxInterval, CFG.tickInterval + 15);
      if (running) { pause(); play(); }
      render();
      break;
    case '\r':
      board[cursorY][cursorX] = board[cursorY][cursorX] ? 0 : 1;
      generation = 0;
      render();
      break;
    case '1': loadPreset('glider'); render(); break;
    case '2': loadPreset('lwss'); render(); break;
    case '3': loadPreset('glider_gun'); render(); break;
    case '4': loadPreset('rpentomino'); render(); break;
    case '5': loadPreset('pulsar'); render(); break;
    case '6': loadPreset('diehard'); render(); break;
    case '7': loadPreset('pentadecathlon'); render(); break;
    case 'q':
    case '\x1b':  // would have been caught above but just in case
    case '\x03':
      cleanup();
      process.exit();
      break;
  }
}

// ─── Game Logic ──────────────────────────────────────────────────────────────

function tick() {
  for (let y = 0; y < rows; y++) {
    for (let x = 0; x < cols; x++) {
      const n = neighbours(y, x);
      if (board[y][x]) {
        nextBoard[y][x] = (n === 2 || n === 3) ? 1 : 0;
      } else {
        nextBoard[y][x] = (n === 3) ? 1 : 0;
      }
    }
  }
  [board, nextBoard] = [nextBoard, board];
  generation++;
  render();
}

function neighbours(y, x) {
  let count = 0;
  for (let dy = -1; dy <= 1; dy++) {
    const ny = (y + dy + rows) % rows;
    for (let dx = -1; dx <= 1; dx++) {
      if (dy === 0 && dx === 0) continue;
      const nx = (x + dx + cols) % cols;
      count += board[ny][nx];
    }
  }
  return count;
}

function play() {
  if (running) return;
  running = true;
  tickTimer = setInterval(tick, CFG.tickInterval);
}

function pause() {
  running = false;
  if (tickTimer) { clearInterval(tickTimer); tickTimer = null; }
}

// ─── Presets ─────────────────────────────────────────────────────────────────

function clearBoard() {
  for (let y = 0; y < rows; y++) board[y].fill(0);
  generation = 0;
}

function randomise() {
  for (let y = 0; y < rows; y++)
    for (let x = 0; x < cols; x++)
      board[y][x] = Math.random() < 0.3 ? 1 : 0;
}

function placePattern(cy, cx, cells) {
  for (const [dy, dx] of cells) {
    const y = cy + dy, x = cx + dx;
    if (y >= 0 && y < rows && x >= 0 && x < cols) board[y][x] = 1;
  }
}

function loadPreset(name) {
  const cy = Math.floor(rows / 2);
  const cx = Math.floor(cols / 2);
  clearBoard();
  switch (name) {
    case 'glider':
      placePattern(cy - 1, cx - 1, [[0,1],[1,2],[2,0],[2,1],[2,2]]);
      break;
    case 'lwss':
      placePattern(cy - 2, cx - 3, [
        [0,1],[0,4],
        [1,0],
        [1,0],[1,4],
        [2,4],[3,4],
        [4,0],[4,3],
      ]);
      break;
    case 'glider_gun':
      placePattern(cy - 4, cx - 18, [
        [0,24],[1,22],[1,24],[2,12],[2,13],[2,20],[2,21],[2,34],[2,35],
        [3,11],[3,15],[3,20],[3,21],[3,34],[3,35],[4,0],[4,1],[4,10],[4,16],[4,20],[4,21],
        [5,0],[5,1],[5,10],[5,14],[5,16],[5,17],[5,22],[5,24],[6,10],[6,16],[6,24],
        [7,11],[7,15],[8,12],[8,13],
      ]);
      break;
    case 'rpentomino':
      placePattern(cy, cx, [[0,1],[0,2],[1,0],[1,1],[2,1]]);
      break;
    case 'pulsar':
      for (const [dx, yBase] of [[2,0],[8,0],[2,5],[8,5],[2,7],[8,7],[2,12],[8,12]]) {
        for (let i = 0; i < 3; i++) {
          placePattern(cy - 6 + yBase + i, cx - 6, [[0, dx]]);
          placePattern(cy - 6 + yBase + i, cx + 4, [[0, dx]]);
        }
      }
      for (const [dy, xBase] of [[2,0],[8,0],[2,5],[8,5],[2,7],[8,7],[2,12],[8,12]]) {
        for (let i = 0; i < 3; i++) {
          placePattern(cy - 6, cx - 6 + xBase + i, [[dy, 0]]);
          placePattern(cy + 4, cx - 6 + xBase + i, [[dy, 0]]);
        }
      }
      break;
    case 'diehard':
      placePattern(cy - 1, cx - 4, [[0,6],[1,0],[1,1],[2,1],[2,5],[2,6],[2,7]]);
      break;
    case 'pentadecathlon':
      for (let i = 0; i < 10; i++) {
        placePattern(cy - 4 + i, cx, [[0,0]]);
      }
      break;
  }
  generation = 0;
  cursorX = cx; cursorY = cy;
}

// ─── Rendering ───────────────────────────────────────────────────────────────

function render() {
  const lines = [];
  const { aliveColor, deadColor, statsColor, titleColor, reset, borderColor, helpColor } = CFG;

  // Title bar
  const title = ' Conway\'s Game of Life ';
  const status = running
    ? `${titleColor}▶ ${statsColor}Running`
    : `${titleColor}⏸  ${statsColor}Paused`;
  const speedTxt = `${statsColor}Speed: ${Math.round(1000 / CFG.tickInterval)} gen/s`;
  const genTxt = `Gen: ${generation.toLocaleString()}`;
  const aliveCount = board.reduce((s, r) => s + r.reduce((a, c) => a + c, 0), 0);
  const popTxt = `Pop: ${aliveCount}`;

  const topBar = `${borderColor}╔${'═'.repeat(cols * 2 + 1)}╗${reset}`;
  const barContent = `${borderColor}║${reset} ${titleColor}${title}${speedTxt}  ${genTxt}  ${popTxt}  ${status}`;
  const padLen = Math.max(0, (cols * 2 + 1) - stripAnsi(title) - stripAnsi(speedTxt) - stripAnsi(genTxt) - stripAnsi(popTxt) - stripAnsi(status) - 3);
  lines.push(`${topBar}\n${barContent}${' '.repeat(padLen)}${borderColor}║${reset}`);

  // Column numbers
  let colNums = `${borderColor}║ ${reset}`;
  for (let x = 0; x < cols; x++) {
    if (x % 5 === 0 || x === cursorX) {
      colNums += `${statsColor}${String(x % 10)}${reset} `;
    } else {
      colNums += '  ';
    }
  }
  lines.push(`${colNums}${borderColor}║${reset}`);

  // Board start
  lines.push(`${borderColor}╔${'═'.repeat(cols * 2 + 1)}╗${reset}`);

  // Grid
  for (let y = 0; y < rows; y++) {
    let line = `${borderColor}║${reset}`;
    for (let x = 0; x < cols; x++) {
      const isCursor = (x === cursorX && y === cursorY) && !running;
      const alive = board[y][x];
      if (isCursor) {
        line += `${CFG.cursorColor}${alive ? aliveColor : deadColor}${alive ? CFG.cellChar : '▚'}${reset}`;
      } else if (alive) {
        line += `${aliveColor}${CFG.cellChar}${reset}`;
      } else {
        line += `${deadColor}${CFG.deadChar}${reset}`;
      }
      line += ' ';
    }
    line += `${borderColor}║${reset}`;
    lines.push(line);
  }

  // Bottom border
  lines.push(`${borderColor}╚${'═'.repeat(cols * 2 + 1)}╝${reset}`);

  // Help bar
  const helpLine = `${helpColor}  [Space] Play/Pause  [R] Random  [C] Clear  [1-7] Presets  [+/-] Speed  [Arrows] Move  [Enter/Click] Draw  [Q] Quit${reset}`;
  lines.push(helpLine);

  stdout.write(`\x1b[H${lines.join('\n')}`);
}

function stripAnsi(s) {
  return s.replace(/\x1b\[[0-9;]*m/g, '');
}

// ─── Boot ────────────────────────────────────────────────────────────────────

setup();
randomise();
render();

process.stdout.write(`\n${CFG.titleColor}  Press Space to start, Q to quit${CFG.reset}`);
