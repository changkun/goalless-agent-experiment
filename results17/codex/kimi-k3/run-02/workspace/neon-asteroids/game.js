"use strict";

const canvas = document.getElementById("game");
const ctx = canvas.getContext("2d");
const scoreEl = document.getElementById("score");
const livesEl = document.getElementById("lives");
const waveEl = document.getElementById("wave");
const overlayEl = document.getElementById("overlay");

const TAU = Math.PI * 2;
const SHIP_RADIUS = 12;
const BULLET_SPEED = 520;
const BULLET_LIFE = 0.9;
const FIRE_COOLDOWN = 0.18;
const THRUST = 340;
const TURN_SPEED = 4.6;
const FRICTION = 0.35;
const INVULN_TIME = 2.5;

let width = 0;
let height = 0;
let state = "menu";
let lastTime = 0;
let hue = 190;
let score = 0;
let lives = 3;
let wave = 0;
let fireTimer = 0;
let hyperspaceCooldown = 0;
let shake = 0;
let waveBannerTimer = 0;

let ship = null;
let bullets = [];
let asteroids = [];
let particles = [];
let stars = [];

const keys = new Set();

function resize() {
  width = canvas.width = window.innerWidth;
  height = canvas.height = window.innerHeight;
  buildStars();
}

function buildStars() {
  stars = [];
  const count = Math.floor((width * height) / 9000);
  for (let i = 0; i < count; i++) {
    stars.push({
      x: Math.random() * width,
      y: Math.random() * height,
      size: Math.random() * 1.6 + 0.3,
      depth: Math.random() * 0.8 + 0.2,
      twinkle: Math.random() * TAU,
    });
  }
}

function wrap(entity) {
  if (entity.x < -entity.r) entity.x += width + entity.r * 2;
  if (entity.x > width + entity.r) entity.x -= width + entity.r * 2;
  if (entity.y < -entity.r) entity.y += height + entity.r * 2;
  if (entity.y > height + entity.r) entity.y -= height + entity.r * 2;
}

function makeShip() {
  return {
    x: width / 2,
    y: height / 2,
    vx: 0,
    vy: 0,
    angle: -Math.PI / 2,
    r: SHIP_RADIUS,
    invuln: INVULN_TIME,
    thrusting: false,
  };
}

function makeAsteroid(x, y, size) {
  const verts = [];
  const vertCount = 8 + Math.floor(Math.random() * 5);
  for (let i = 0; i < vertCount; i++) {
    verts.push({
      angle: (i / vertCount) * TAU,
      radius: size * (0.7 + Math.random() * 0.5),
    });
  }
  const speed = 40 + Math.random() * 70 + wave * 8;
  const dir = Math.random() * TAU;
  return {
    x: x,
    y: y,
    vx: Math.cos(dir) * speed,
    vy: Math.sin(dir) * speed,
    r: size,
    size: size,
    verts: verts,
    spin: (Math.random() - 0.5) * 2,
    rot: Math.random() * TAU,
  };
}

function spawnWave() {
  wave++;
  waveBannerTimer = 2;
  const count = 3 + wave;
  for (let i = 0; i < count; i++) {
    let x = 0;
    let y = 0;
    do {
      x = Math.random() * width;
      y = Math.random() * height;
    } while (ship && Math.hypot(x - ship.x, y - ship.y) < 180);
    asteroids.push(makeAsteroid(x, y, 42 + Math.random() * 14));
  }
  updateHud();
}

function explode(x, y, count, color, speed) {
  for (let i = 0; i < count; i++) {
    const dir = Math.random() * TAU;
    const vel = (Math.random() * 0.6 + 0.4) * speed;
    particles.push({
      x: x,
      y: y,
      vx: Math.cos(dir) * vel,
      vy: Math.sin(dir) * vel,
      life: 0.5 + Math.random() * 0.7,
      maxLife: 1.2,
      color: color,
      size: Math.random() * 2.5 + 1,
    });
  }
}

function fire() {
  if (fireTimer > 0) return;
  fireTimer = FIRE_COOLDOWN;
  const nose = SHIP_RADIUS + 4;
  bullets.push({
    x: ship.x + Math.cos(ship.angle) * nose,
    y: ship.y + Math.sin(ship.angle) * nose,
    vx: Math.cos(ship.angle) * BULLET_SPEED + ship.vx,
    vy: Math.sin(ship.angle) * BULLET_SPEED + ship.vy,
    r: 2.5,
    life: BULLET_LIFE,
  });
}

function hyperspace() {
  if (hyperspaceCooldown > 0) return;
  hyperspaceCooldown = 3;
  explode(ship.x, ship.y, 25, "#4df3ff", 200);
  ship.x = Math.random() * width;
  ship.y = Math.random() * height;
  ship.vx = 0;
  ship.vy = 0;
  ship.invuln = Math.max(ship.invuln, 1);
  explode(ship.x, ship.y, 25, "#ff4dd8", 200);
}

function splitAsteroid(rock) {
  if (rock.size > 30) {
    for (let i = 0; i < 2; i++) asteroids.push(makeAsteroid(rock.x, rock.y, rock.size * 0.6));
  } else if (rock.size > 15) {
    for (let i = 0; i < 2; i++) asteroids.push(makeAsteroid(rock.x, rock.y, rock.size * 0.55));
  }
}

function scoreFor(size) {
  if (size > 30) return 20;
  if (size > 15) return 50;
  return 100;
}

function hitShip() {
  if (ship.invuln > 0) return;
  explode(ship.x, ship.y, 60, "#ff4dd8", 320);
  shake = 18;
  lives--;
  if (lives <= 0) {
    state = "gameover";
    ship = null;
    showOverlay("GAME OVER", "FINAL SCORE " + score, "PRESS ENTER TO RETRY");
  } else {
    ship = makeShip();
  }
  updateHud();
}

function update(dt) {
  hue = (hue + dt * 12) % 360;
  fireTimer -= dt;
  hyperspaceCooldown -= dt;
  shake = Math.max(0, shake - dt * 40);
  waveBannerTimer = Math.max(0, waveBannerTimer - dt);

  if (ship) {
    ship.invuln -= dt;
    ship.thrusting = keys.has("ArrowUp") || keys.has("KeyW");
    if (keys.has("Space")) fire();
    if (keys.has("ArrowLeft") || keys.has("KeyA")) ship.angle -= TURN_SPEED * dt;
    if (keys.has("ArrowRight") || keys.has("KeyD")) ship.angle += TURN_SPEED * dt;
    if (ship.thrusting) {
      ship.vx += Math.cos(ship.angle) * THRUST * dt;
      ship.vy += Math.sin(ship.angle) * THRUST * dt;
      particles.push({
        x: ship.x - Math.cos(ship.angle) * SHIP_RADIUS,
        y: ship.y - Math.sin(ship.angle) * SHIP_RADIUS,
        vx: -Math.cos(ship.angle) * 120 + (Math.random() - 0.5) * 60,
        vy: -Math.sin(ship.angle) * 120 + (Math.random() - 0.5) * 60,
        life: 0.3,
        maxLife: 0.3,
        color: "#ffb347",
        size: Math.random() * 2 + 1,
      });
    }
    ship.vx -= ship.vx * FRICTION * dt;
    ship.vy -= ship.vy * FRICTION * dt;
    ship.x += ship.vx * dt;
    ship.y += ship.vy * dt;
    wrap(ship);
  }

  for (let i = bullets.length - 1; i >= 0; i--) {
    const b = bullets[i];
    b.x += b.vx * dt;
    b.y += b.vy * dt;
    b.life -= dt;
    wrap(b);
    if (b.life <= 0) bullets.splice(i, 1);
  }

  for (const rock of asteroids) {
    rock.x += rock.vx * dt;
    rock.y += rock.vy * dt;
    rock.rot += rock.spin * dt;
    wrap(rock);
  }

  for (let i = particles.length - 1; i >= 0; i--) {
    const p = particles[i];
    p.x += p.vx * dt;
    p.y += p.vy * dt;
    p.life -= dt;
    if (p.life <= 0) particles.splice(i, 1);
  }

  for (let i = asteroids.length - 1; i >= 0; i--) {
    const rock = asteroids[i];
    let destroyed = false;
    for (let j = bullets.length - 1; j >= 0; j--) {
      const b = bullets[j];
      if (Math.hypot(b.x - rock.x, b.y - rock.y) < rock.r + b.r) {
        bullets.splice(j, 1);
        asteroids.splice(i, 1);
        splitAsteroid(rock);
        explode(rock.x, rock.y, 22, "hsl(" + hue + ", 100%, 65%)", 240);
        score += scoreFor(rock.size);
        shake = Math.max(shake, 6);
        destroyed = true;
        updateHud();
        break;
      }
    }
    if (destroyed) continue;
    if (ship && ship.invuln <= 0 &&
        Math.hypot(ship.x - rock.x, ship.y - rock.y) < rock.r + ship.r * 0.8) {
      hitShip();
      break;
    }
  }

  if (state === "playing" && asteroids.length === 0) spawnWave();
}

function neonStroke(color, blur, widthPx, pathFn) {
  ctx.save();
  ctx.strokeStyle = color;
  ctx.lineWidth = widthPx;
  ctx.shadowColor = color;
  ctx.shadowBlur = blur;
  ctx.beginPath();
  pathFn();
  ctx.stroke();
  ctx.stroke();
  ctx.restore();
}

function drawStars(time) {
  ctx.save();
  for (const s of stars) {
    const alpha = 0.3 + 0.5 * s.depth * (0.6 + 0.4 * Math.sin(time * 0.002 * s.depth + s.twinkle));
    ctx.fillStyle = "rgba(200, 230, 255, " + alpha + ")";
    ctx.fillRect(s.x, s.y, s.size, s.size);
  }
  ctx.restore();
}

function drawShip() {
  if (!ship) return;
  if (ship.invuln > 0 && Math.floor(ship.invuln * 10) % 2 === 0) return;
  const color = "#4df3ff";
  neonStroke(color, 14, 2, function () {
    ctx.moveTo(Math.cos(ship.angle) * (SHIP_RADIUS + 6) + ship.x,
               Math.sin(ship.angle) * (SHIP_RADIUS + 6) + ship.y);
    ctx.lineTo(Math.cos(ship.angle + 2.5) * SHIP_RADIUS + ship.x,
               Math.sin(ship.angle + 2.5) * SHIP_RADIUS + ship.y);
    ctx.lineTo(Math.cos(ship.angle + Math.PI) * SHIP_RADIUS * 0.5 + ship.x,
               Math.sin(ship.angle + Math.PI) * SHIP_RADIUS * 0.5 + ship.y);
    ctx.lineTo(Math.cos(ship.angle - 2.5) * SHIP_RADIUS + ship.x,
               Math.sin(ship.angle - 2.5) * SHIP_RADIUS + ship.y);
    ctx.closePath();
  });
  if (ship.thrusting) {
    const flicker = 1 + Math.random() * 0.4;
    neonStroke("#ffb347", 12, 2, function () {
      ctx.moveTo(ship.x + Math.cos(ship.angle + 2.7) * SHIP_RADIUS * 0.8,
                 ship.y + Math.sin(ship.angle + 2.7) * SHIP_RADIUS * 0.8);
      ctx.lineTo(ship.x + Math.cos(ship.angle + Math.PI) * SHIP_RADIUS * 1.8 * flicker,
                 ship.y + Math.sin(ship.angle + Math.PI) * SHIP_RADIUS * 1.8 * flicker);
      ctx.lineTo(ship.x + Math.cos(ship.angle - 2.7) * SHIP_RADIUS * 0.8,
                 ship.y + Math.sin(ship.angle - 2.7) * SHIP_RADIUS * 0.8);
    });
  }
}

function drawAsteroid(rock) {
  const color = "hsl(" + hue + ", 100%, 65%)";
  neonStroke(color, 12, 2, function () {
    rock.verts.forEach(function (v, i) {
      const a = v.angle + rock.rot;
      const px = rock.x + Math.cos(a) * v.radius;
      const py = rock.y + Math.sin(a) * v.radius;
      if (i === 0) ctx.moveTo(px, py);
      else ctx.lineTo(px, py);
    });
    ctx.closePath();
  });
}

function draw() {
  ctx.clearRect(0, 0, width, height);
  ctx.save();
  if (shake > 0) {
    ctx.translate((Math.random() - 0.5) * shake, (Math.random() - 0.5) * shake);
  }

  drawStars(performance.now());

  for (const rock of asteroids) drawAsteroid(rock);

  for (const b of bullets) {
    ctx.save();
    ctx.fillStyle = "#fff";
    ctx.shadowColor = "#4df3ff";
    ctx.shadowBlur = 10;
    ctx.beginPath();
    ctx.arc(b.x, b.y, b.r, 0, TAU);
    ctx.fill();
    ctx.restore();
  }

  for (const p of particles) {
    const alpha = Math.max(p.life / p.maxLife, 0);
    ctx.save();
    ctx.globalAlpha = alpha;
    ctx.fillStyle = p.color;
    ctx.shadowColor = p.color;
    ctx.shadowBlur = 8;
    ctx.fillRect(p.x - p.size / 2, p.y - p.size / 2, p.size, p.size);
    ctx.restore();
  }

  drawShip();
  ctx.restore();

  if (waveBannerTimer > 0 && state === "playing") {
    ctx.save();
    ctx.globalAlpha = Math.min(waveBannerTimer, 1);
    ctx.fillStyle = "#ffb347";
    ctx.shadowColor = "#ffb347";
    ctx.shadowBlur = 20;
    ctx.font = "bold 42px 'Courier New', monospace";
    ctx.textAlign = "center";
    ctx.fillText("WAVE " + wave, width / 2, height / 2 - 40);
    ctx.restore();
  }

  if (state === "paused") {
    ctx.save();
    ctx.fillStyle = "rgba(5, 6, 14, 0.6)";
    ctx.fillRect(0, 0, width, height);
    ctx.fillStyle = "#4df3ff";
    ctx.shadowColor = "#4df3ff";
    ctx.shadowBlur = 24;
    ctx.font = "bold 48px 'Courier New', monospace";
    ctx.textAlign = "center";
    ctx.fillText("PAUSED", width / 2, height / 2);
    ctx.restore();
  }
}

function updateHud() {
  scoreEl.textContent = "SCORE " + score;
  livesEl.innerHTML = "&#10084;".repeat(Math.max(lives, 0)) || "&#9760;";
  waveEl.textContent = "WAVE " + Math.max(wave, 1);
}

function showOverlay(title, subtitle, prompt) {
  overlayEl.querySelector("h1").textContent = title;
  overlayEl.querySelector("p").innerHTML = subtitle;
  overlayEl.querySelector(".blink").textContent = prompt;
  overlayEl.classList.remove("hidden");
}

function startGame() {
  score = 0;
  lives = 3;
  wave = 0;
  bullets = [];
  asteroids = [];
  particles = [];
  ship = makeShip();
  state = "playing";
  overlayEl.classList.add("hidden");
  spawnWave();
  updateHud();
}

function loop(time) {
  const dt = Math.min((time - lastTime) / 1000, 0.05);
  lastTime = time;
  if (state === "playing") update(dt);
  draw();
  requestAnimationFrame(loop);
}

window.addEventListener("keydown", function (e) {
  if (["ArrowUp", "ArrowDown", "ArrowLeft", "ArrowRight", "Space"].indexOf(e.code) !== -1) {
    e.preventDefault();
  }
  if (e.code === "Enter" && (state === "menu" || state === "gameover")) {
    startGame();
    return;
  }
  if (e.code === "KeyP" && (state === "playing" || state === "paused")) {
    state = state === "playing" ? "paused" : "playing";
    return;
  }
  if (state !== "playing") return;
  keys.add(e.code);
  if (e.code === "Space") fire();
  if (e.code === "ShiftLeft" || e.code === "ShiftRight") hyperspace();
});

window.addEventListener("keyup", function (e) { keys.delete(e.code); });
window.addEventListener("blur", function () { keys.clear(); });
window.addEventListener("resize", resize);

resize();
requestAnimationFrame(loop);
