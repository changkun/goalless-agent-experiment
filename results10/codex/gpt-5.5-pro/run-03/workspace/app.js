"use strict";

const COLS = 16;
const ROWS = 8;
const STORAGE_KEY = "pulse-grid-state-v1";

const scales = {
  minor: [0, 2, 3, 5, 7, 8, 10, 12],
  major: [0, 2, 4, 5, 7, 9, 11, 12],
  dorian: [0, 2, 3, 5, 7, 9, 10, 12],
  pentatonic: [0, 2, 4, 7, 9, 12, 14, 16],
  chromatic: [0, 1, 2, 3, 4, 5, 6, 7],
};

const noteNames = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"];

const elements = {
  grid: document.querySelector("#grid"),
  stepMarkers: document.querySelector("#stepMarkers"),
  playToggle: document.querySelector("#playToggle"),
  statusText: document.querySelector("#statusText"),
  stepReadout: document.querySelector("#stepReadout"),
  randomize: document.querySelector("#randomize"),
  clearPattern: document.querySelector("#clearPattern"),
  density: document.querySelector("#density"),
  densityValue: document.querySelector("#densityValue"),
  tempo: document.querySelector("#tempo"),
  tempoValue: document.querySelector("#tempoValue"),
  swing: document.querySelector("#swing"),
  swingValue: document.querySelector("#swingValue"),
  root: document.querySelector("#root"),
  scale: document.querySelector("#scale"),
  wave: document.querySelector("#wave"),
  volume: document.querySelector("#volume"),
  volumeValue: document.querySelector("#volumeValue"),
  scope: document.querySelector("#scope"),
};

const defaultPattern = [
  "1000100010001000",
  "0000000000000000",
  "0010001000100010",
  "0000000010000000",
  "0100010001000100",
  "0001000000010000",
  "1000000010000000",
  "0000100000001000",
].map((row) => row.split("").map((cell) => cell === "1"));

const state = loadState();
const cellButtons = Array.from({ length: ROWS }, () => Array(COLS).fill(null));
const noteLabels = Array(ROWS).fill(null);
const visualPulses = Array(COLS).fill(0);

let audioContext = null;
let masterGain = null;
let timerId = null;
let currentStep = -1;
let isPainting = false;
let paintValue = false;
let suppressedClickTarget = null;

function clonePattern(pattern) {
  return pattern.map((row) => row.slice());
}

function createEmptyPattern() {
  return Array.from({ length: ROWS }, () => Array(COLS).fill(false));
}

function isValidPattern(pattern) {
  return Array.isArray(pattern)
    && pattern.length === ROWS
    && pattern.every((row) => Array.isArray(row) && row.length === COLS && row.every((cell) => typeof cell === "boolean"));
}

function loadState() {
  const fallback = {
    pattern: clonePattern(defaultPattern),
    tempo: 112,
    swing: 12,
    density: 30,
    root: 0,
    scale: "minor",
    wave: "sine",
    volume: 34,
  };

  try {
    const saved = JSON.parse(localStorage.getItem(STORAGE_KEY) || "null");
    if (!saved || typeof saved !== "object") {
      return fallback;
    }

    return {
      pattern: isValidPattern(saved.pattern) ? saved.pattern : fallback.pattern,
      tempo: clampNumber(saved.tempo, 60, 180, fallback.tempo),
      swing: clampNumber(saved.swing, 0, 60, fallback.swing),
      density: clampNumber(saved.density, 8, 70, fallback.density),
      root: clampNumber(saved.root, 0, 11, fallback.root),
      scale: Object.hasOwn(scales, saved.scale) ? saved.scale : fallback.scale,
      wave: ["sine", "triangle", "square", "sawtooth"].includes(saved.wave) ? saved.wave : fallback.wave,
      volume: clampNumber(saved.volume, 0, 80, fallback.volume),
    };
  } catch {
    return fallback;
  }
}

function saveState() {
  const serializable = {
    pattern: state.pattern,
    tempo: state.tempo,
    swing: state.swing,
    density: state.density,
    root: state.root,
    scale: state.scale,
    wave: state.wave,
    volume: state.volume,
  };
  try {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(serializable));
  } catch {
    // Pattern memory is a convenience; the sequencer should still work without storage.
  }
}

function clampNumber(value, min, max, fallback) {
  const number = Number(value);
  if (!Number.isFinite(number)) {
    return fallback;
  }
  return Math.min(max, Math.max(min, Math.round(number)));
}

function midiToFrequency(midi) {
  return 440 * 2 ** ((midi - 69) / 12);
}

function getRowMidi(row) {
  const intervals = scales[state.scale] || scales.minor;
  const interval = intervals[ROWS - 1 - row];
  return 48 + state.root + interval;
}

function getNoteLabel(row) {
  const midi = getRowMidi(row);
  const pitch = noteNames[((midi % 12) + 12) % 12];
  const octave = Math.floor(midi / 12) - 1;
  return `${pitch}${octave}`;
}

function buildStepMarkers() {
  elements.stepMarkers.textContent = "";
  const spacer = document.createElement("div");
  elements.stepMarkers.append(spacer);

  for (let col = 0; col < COLS; col += 1) {
    const marker = document.createElement("div");
    marker.className = "step-marker";
    marker.textContent = col % 4 === 0 ? String(col + 1).padStart(2, "0") : "";
    elements.stepMarkers.append(marker);
  }
}

function buildGrid() {
  elements.grid.textContent = "";

  for (let row = 0; row < ROWS; row += 1) {
    const label = document.createElement("div");
    label.className = "note-label";
    noteLabels[row] = label;
    elements.grid.append(label);

    for (let col = 0; col < COLS; col += 1) {
      const cell = document.createElement("button");
      cell.className = "grid-cell";
      cell.type = "button";
      cell.dataset.row = String(row);
      cell.dataset.col = String(col);
      cell.setAttribute("role", "gridcell");

      cell.addEventListener("pointerdown", (event) => {
        if (event.button !== 0) {
          return;
        }
        event.preventDefault();
        isPainting = true;
        paintValue = !state.pattern[row][col];
        suppressedClickTarget = cell;
        setCell(row, col, paintValue);
      });

      cell.addEventListener("pointerenter", () => {
        if (isPainting) {
          setCell(row, col, paintValue);
        }
      });

      cell.addEventListener("click", (event) => {
        if (suppressedClickTarget === cell) {
          suppressedClickTarget = null;
          event.preventDefault();
          return;
        }
        setCell(row, col, !state.pattern[row][col]);
      });

      cellButtons[row][col] = cell;
      elements.grid.append(cell);
    }
  }

  document.addEventListener("pointerup", () => {
    isPainting = false;
    window.setTimeout(() => {
      suppressedClickTarget = null;
    }, 0);
  });
}

function setCell(row, col, value) {
  state.pattern[row][col] = value;
  renderCell(row, col);
  saveState();
}

function renderCell(row, col) {
  const cell = cellButtons[row][col];
  const active = state.pattern[row][col];
  const note = getNoteLabel(row);
  cell.classList.toggle("is-on", active);
  cell.classList.toggle("is-current", col === currentStep);
  cell.setAttribute("aria-pressed", String(active));
  cell.setAttribute("aria-label", `${note}, step ${col + 1}, ${active ? "on" : "off"}`);
}

function renderGrid() {
  for (let row = 0; row < ROWS; row += 1) {
    noteLabels[row].textContent = getNoteLabel(row);
    for (let col = 0; col < COLS; col += 1) {
      renderCell(row, col);
    }
  }
}

function renderControls() {
  elements.tempo.value = String(state.tempo);
  elements.tempoValue.value = String(state.tempo);
  elements.swing.value = String(state.swing);
  elements.swingValue.value = `${state.swing}%`;
  elements.density.value = String(state.density);
  elements.densityValue.value = `${state.density}%`;
  elements.root.value = String(state.root);
  elements.scale.value = state.scale;
  elements.wave.value = state.wave;
  elements.volume.value = String(state.volume);
  elements.volumeValue.value = `${state.volume}%`;
  updateMasterGain();
}

function updateTransport() {
  const playing = Boolean(timerId);
  elements.playToggle.classList.toggle("is-playing", playing);
  elements.playToggle.setAttribute("aria-label", playing ? "Pause" : "Play");
  elements.playToggle.title = playing ? "Pause" : "Play";
  elements.statusText.textContent = playing ? `${state.tempo} BPM` : "Stopped";
  elements.stepReadout.value = String(Math.max(0, currentStep) + 1).padStart(2, "0");
}

function clearHighlights(previousStep) {
  if (previousStep < 0) {
    return;
  }
  for (let row = 0; row < ROWS; row += 1) {
    cellButtons[row][previousStep].classList.remove("is-current");
  }
}

function showStep(step) {
  for (let row = 0; row < ROWS; row += 1) {
    cellButtons[row][step].classList.add("is-current");
  }
  elements.stepReadout.value = String(step + 1).padStart(2, "0");
}

async function ensureAudio() {
  if (!audioContext) {
    const AudioContextClass = window.AudioContext || window.webkitAudioContext;
    if (!AudioContextClass) {
      throw new Error("Web Audio is unavailable in this browser.");
    }
    audioContext = new AudioContextClass();
    masterGain = audioContext.createGain();
    masterGain.connect(audioContext.destination);
    updateMasterGain();
  }

  if (audioContext.state === "suspended") {
    await audioContext.resume();
  }
}

function updateMasterGain() {
  if (!masterGain || !audioContext) {
    return;
  }
  const target = state.volume / 100;
  masterGain.gain.setTargetAtTime(target, audioContext.currentTime, 0.02);
}

function playNote(row, activeCount) {
  if (!audioContext || !masterGain) {
    return;
  }

  const now = audioContext.currentTime;
  const oscillator = audioContext.createOscillator();
  const gain = audioContext.createGain();
  const frequency = midiToFrequency(getRowMidi(row));
  const level = Math.min(0.28, 0.18 / Math.max(1, activeCount));
  const duration = Math.max(0.08, (60 / state.tempo) * 0.48);

  oscillator.type = state.wave;
  oscillator.frequency.setValueAtTime(frequency, now);
  gain.gain.setValueAtTime(0.0001, now);
  gain.gain.exponentialRampToValueAtTime(level, now + 0.012);
  gain.gain.exponentialRampToValueAtTime(0.0001, now + duration);

  oscillator.connect(gain);
  gain.connect(masterGain);
  oscillator.start(now);
  oscillator.stop(now + duration + 0.03);
}

function playStep(step) {
  const activeRows = [];
  for (let row = 0; row < ROWS; row += 1) {
    if (state.pattern[row][step]) {
      activeRows.push(row);
    }
  }

  activeRows.forEach((row) => playNote(row, activeRows.length));
  visualPulses[step] = activeRows.length ? Math.min(1, 0.25 + activeRows.length * 0.16) : 0.16;
}

function getStepDelay(step) {
  const base = 60000 / state.tempo / 4;
  const swingOffset = base * (state.swing / 100) * 0.5;
  return step % 2 === 0 ? base + swingOffset : base - swingOffset;
}

function tick() {
  const previousStep = currentStep;
  currentStep = (currentStep + 1) % COLS;
  clearHighlights(previousStep);
  showStep(currentStep);
  playStep(currentStep);
  updateTransport();
  timerId = window.setTimeout(tick, getStepDelay(currentStep));
}

async function startPlayback() {
  await ensureAudio();
  if (timerId) {
    return;
  }
  tick();
}

function stopPlayback() {
  if (timerId) {
    window.clearTimeout(timerId);
    timerId = null;
  }
  updateTransport();
}

function clearPattern() {
  state.pattern = createEmptyPattern();
  renderGrid();
  saveState();
}

function randomizePattern() {
  const density = state.density / 100;
  for (let row = 0; row < ROWS; row += 1) {
    for (let col = 0; col < COLS; col += 1) {
      const downbeatLift = col % 4 === 0 ? 0.08 : 0;
      const upperTrim = row < 2 ? -0.08 : 0;
      state.pattern[row][col] = Math.random() < Math.max(0.03, density + downbeatLift + upperTrim);
    }
  }
  renderGrid();
  saveState();
}

function bindControls() {
  elements.playToggle.addEventListener("click", () => {
    if (timerId) {
      stopPlayback();
    } else {
      startPlayback().catch(() => {
        elements.statusText.textContent = "Audio unavailable";
      });
    }
  });

  elements.randomize.addEventListener("click", randomizePattern);
  elements.clearPattern.addEventListener("click", clearPattern);

  bindRange(elements.tempo, elements.tempoValue, "", (value) => {
    state.tempo = value;
    updateTransport();
  });
  bindRange(elements.swing, elements.swingValue, "%", (value) => {
    state.swing = value;
  });
  bindRange(elements.density, elements.densityValue, "%", (value) => {
    state.density = value;
  });
  bindRange(elements.volume, elements.volumeValue, "%", (value) => {
    state.volume = value;
    updateMasterGain();
  });

  elements.root.addEventListener("change", () => {
    state.root = Number(elements.root.value);
    renderGrid();
    saveState();
  });

  elements.scale.addEventListener("change", () => {
    state.scale = elements.scale.value;
    renderGrid();
    saveState();
  });

  elements.wave.addEventListener("change", () => {
    state.wave = elements.wave.value;
    saveState();
  });

  window.addEventListener("beforeunload", stopPlayback);
}

function bindRange(input, output, suffix, onInput) {
  input.addEventListener("input", () => {
    const value = Number(input.value);
    output.value = `${value}${suffix}`;
    onInput(value);
    saveState();
  });
}

function drawScope() {
  const canvas = elements.scope;
  const context = canvas.getContext("2d");
  const rect = canvas.getBoundingClientRect();
  const ratio = window.devicePixelRatio || 1;
  const width = Math.max(320, Math.floor(rect.width * ratio));
  const height = Math.max(120, Math.floor(rect.height * ratio));

  if (canvas.width !== width || canvas.height !== height) {
    canvas.width = width;
    canvas.height = height;
  }

  context.clearRect(0, 0, width, height);
  context.fillStyle = "#202420";
  context.fillRect(0, 0, width, height);

  const gutter = 18 * ratio;
  const usableWidth = width - gutter * 2;
  const usableHeight = height - gutter * 2;
  const columnWidth = usableWidth / COLS;
  const centerY = height / 2;

  context.strokeStyle = "rgba(255, 255, 255, 0.18)";
  context.lineWidth = 1 * ratio;
  context.beginPath();
  context.moveTo(gutter, centerY);
  context.lineTo(width - gutter, centerY);
  context.stroke();

  for (let col = 0; col < COLS; col += 1) {
    const pulse = visualPulses[col];
    const x = gutter + col * columnWidth + columnWidth * 0.18;
    const barWidth = Math.max(5 * ratio, columnWidth * 0.64);
    const barHeight = Math.max(8 * ratio, usableHeight * pulse);
    const y = centerY - barHeight / 2;
    context.fillStyle = col === currentStep ? "#f3b23a" : "#089d92";
    context.fillRect(x, y, barWidth, barHeight);
    visualPulses[col] *= 0.92;
  }

  window.requestAnimationFrame(drawScope);
}

function init() {
  buildStepMarkers();
  buildGrid();
  renderGrid();
  renderControls();
  updateTransport();
  bindControls();
  drawScope();
}

init();
