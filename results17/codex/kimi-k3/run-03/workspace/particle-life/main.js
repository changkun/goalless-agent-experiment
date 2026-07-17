/* Particle Life — UI, rendering, and seed handling. */

"use strict";

// ---------- seeded RNG ----------

function xmur3(str) {
  let h = 1779033703 ^ str.length;
  for (let i = 0; i < str.length; i++) {
    h = Math.imul(h ^ str.charCodeAt(i), 3432918353);
    h = (h << 13) | (h >>> 19);
  }
  return function () {
    h = Math.imul(h ^ (h >>> 16), 2246822507);
    h = Math.imul(h ^ (h >>> 13), 3266489909);
    h ^= h >>> 16;
    return h >>> 0;
  };
}

function mulberry32(a) {
  return function () {
    a |= 0;
    a = (a + 0x6d2b79f5) | 0;
    let t = Math.imul(a ^ (a >>> 15), 1 | a);
    t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t;
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
}

function rngFromSeed(seed) {
  return mulberry32(xmur3(seed)());
}

function randomSeed() {
  const words = ["ember", "tide", "moss", "quartz", "nova", "fern", "onyx", "wisp", "cinder", "gale"];
  const pick = () => words[(Math.random() * words.length) | 0];
  return `${pick()}-${pick()}-${(Math.random() * 100) | 0}`;
}

// ---------- canvas ----------

const canvas = document.getElementById("view");
const ctx = canvas.getContext("2d");
let dpr = 1;

function fitCanvas() {
  dpr = Math.min(window.devicePixelRatio || 1, 2);
  canvas.width = Math.floor(window.innerWidth * dpr);
  canvas.height = Math.floor(window.innerHeight * dpr);
  if (sim) sim.resize(window.innerWidth, window.innerHeight);
}

// ---------- simulation state ----------

const params = {
  count: 1200,
  species: 5,
  radius: 80,
  force: 40,
  friction: 0.05,
  speed: 1,
};

let sim = null;
let running = true;

function buildSim(seed) {
  sim = new ParticleLife(window.innerWidth, window.innerHeight, params, rngFromSeed(seed));
  updatePopLabel();
}

function draw() {
  ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
  ctx.fillStyle = "#0b0e14";
  ctx.fillRect(0, 0, window.innerWidth, window.innerHeight);
  const palette = sim.species;
  for (const p of sim.particles) {
    ctx.fillStyle = palette[p.type].color;
    ctx.fillRect(p.x - 1.5, p.y - 1.5, 3, 3);
  }
}

// ---------- main loop ----------

let lastT = performance.now();
let fpsAccum = 0;
let fpsFrames = 0;
let fpsLast = lastT;

function frame(now) {
  const elapsed = Math.min((now - lastT) / 1000, 0.05);
  lastT = now;

  if (running) {
    // Fixed-ish timestep scaled by the speed control.
    const dt = 60 * elapsed * params.speed;
    sim.step(dt);
    draw();
  }

  fpsAccum += elapsed;
  fpsFrames++;
  if (now - fpsLast > 500) {
    const fps = Math.round(fpsFrames / fpsAccum);
    fpsEl.textContent = `${fps} fps`;
    fpsAccum = 0;
    fpsFrames = 0;
    fpsLast = now;
  }
  requestAnimationFrame(frame);
}

// ---------- controls ----------

const $ = (id) => document.getElementById(id);

const seedInput = $("seed");
const fpsEl = $("fps");
const popEl = $("pop");

function updatePopLabel() {
  popEl.textContent = `${sim.particles.length} particles · ${sim.species.length} species`;
}

function bindSlider(id, outId, key, fmt, onChange) {
  const el = $(id);
  const out = $(outId);
  const show = () => { out.textContent = fmt(params[key]); };
  el.value = params[key];
  show();
  el.addEventListener("input", () => {
    params[key] = parseFloat(el.value);
    show();
    if (onChange) onChange();
  });
}

const int = (v) => String(Math.round(v));

bindSlider("count", "countOut", "count", int, () => sim && sim.setCount(params.count));
bindSlider("species", "speciesOut", "species", int, () => {
  if (!sim) return;
  sim.setSpecies(params.species);
  sim.setCount(params.count);
  updatePopLabel();
});
bindSlider("radius", "radiusOut", "radius", (v) => `${int(v)}px`, () => { if (sim) sim.radius = params.radius; });
bindSlider("force", "forceOut", "force", (v) => `${int(v)}×`, () => { if (sim) sim.force = params.force; });
bindSlider("friction", "frictionOut", "friction", (v) => v.toFixed(2), () => { if (sim) sim.friction = params.friction; });
bindSlider("speed", "speedOut", "speed", (v) => `${v.toFixed(1)}×`);

// ---------- seed handling ----------

function loadSeed(seed, pushUrl = true) {
  seed = seed.trim() || randomSeed();
  seedInput.value = seed;
  buildSim(seed);
  if (pushUrl) {
    const url = new URL(window.location.href);
    url.searchParams.set("seed", seed);
    history.replaceState(null, "", url);
  }
  if (!running) draw();
}

$("reseed").addEventListener("click", () => loadSeed(seedInput.value));
$("random").addEventListener("click", () => loadSeed(randomSeed()));
seedInput.addEventListener("keydown", (e) => {
  if (e.key === "Enter") loadSeed(seedInput.value);
});

// ---------- playback ----------

const playBtn = $("play");

function setRunning(v) {
  running = v;
  playBtn.textContent = running ? "Pause" : "Play";
  if (running) lastT = performance.now();
}

playBtn.addEventListener("click", () => setRunning(!running));
$("burst").addEventListener("click", () => {
  sim.burst();
  if (!running) draw();
});

// ---------- panel show/hide ----------

const panel = $("panel");
const expandBtn = $("expand");

function setPanelVisible(visible) {
  panel.classList.toggle("hidden", !visible);
  expandBtn.classList.toggle("hidden", visible);
}

$("collapse").addEventListener("click", () => setPanelVisible(false));
expandBtn.addEventListener("click", () => setPanelVisible(true));

// ---------- keyboard ----------

window.addEventListener("keydown", (e) => {
  if (e.target.tagName === "INPUT") return;
  if (e.code === "Space") { e.preventDefault(); setRunning(!running); }
  else if (e.key === "b" || e.key === "B") { sim.burst(); if (!running) draw(); }
  else if (e.key === "h" || e.key === "H") { setPanelVisible(panel.classList.contains("hidden")); }
});

// ---------- boot ----------

window.addEventListener("resize", fitCanvas);
fitCanvas();
const initialSeed = new URLSearchParams(window.location.search).get("seed") || randomSeed();
loadSeed(initialSeed, false);
draw();
requestAnimationFrame(frame);
