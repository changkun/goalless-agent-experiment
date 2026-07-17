/* Particle Life — physics core.
   Species attract/repel each other via a distance-based force law;
   structure (cells, hunters, swarms) emerges from those simple rules. */

"use strict";

const SPECIES_PALETTE = [
  { name: "ember",  color: "#ff5a47" },
  { name: "amber",  color: "#ff9f43" },
  { name: "lime",   color: "#a3e048" },
  { name: "jade",   color: "#34d399" },
  { name: "azure",  color: "#4cc2ff" },
  { name: "violet", color: "#9d6bff" },
  { name: "rose",   color: "#f368e0" },
];

class ParticleLife {
  constructor(width, height, opts, rng) {
    this.width = width;
    this.height = height;
    this.radius = opts.radius;   // interaction radius (px)
    this.force = opts.force;     // global force multiplier
    this.friction = opts.friction; // velocity damping per tick
    this.rng = rng;
    this.setSpecies(opts.species);
    this.setCount(opts.count);
  }

  setSpecies(n) {
    this.species = SPECIES_PALETTE.slice(0, n);
    // Random asymmetric force matrix in [-1, 1]. This matrix IS the genome
    // of the universe — every rule of who chases whom lives here.
    this.matrix = [];
    for (let i = 0; i < n; i++) {
      const row = [];
      for (let j = 0; j < n; j++) row.push(this.rng() * 2 - 1);
      this.matrix.push(row);
    }
  }

  setCount(count) {
    const n = this.species.length;
    this.particles = [];
    for (let i = 0; i < count; i++) {
      this.particles.push({
        x: this.rng() * this.width,
        y: this.rng() * this.height,
        vx: 0,
        vy: 0,
        type: i % n,
      });
    }
  }

  resize(width, height) {
    this.width = width;
    this.height = height;
    for (const p of this.particles) {
      if (p.x > width) p.x = this.rng() * width;
      if (p.y > height) p.y = this.rng() * height;
    }
  }

  // Kick a burst of kinetic energy into the mix.
  burst(strength = 6) {
    for (const p of this.particles) {
      p.vx += (this.rng() * 2 - 1) * strength;
      p.vy += (this.rng() * 2 - 1) * strength;
    }
  }

  step(dt) {
    const { particles, matrix, width, height, radius, force, friction } = this;
    const count = particles.length;
    const r2 = radius * radius;
    const damping = Math.max(0, 1 - friction * dt);

    // Spatial hash grid: cell size = radius, so each particle only checks
    // its own cell + the 8 neighbours. O(n) instead of O(n^2).
    const cellSize = radius;
    const cols = Math.max(1, Math.ceil(width / cellSize));
    const rows = Math.max(1, Math.ceil(height / cellSize));
    const grid = new Array(cols * rows);
    for (let i = 0; i < count; i++) {
      const p = particles[i];
      let cx = (p.x / cellSize) | 0;
      let cy = (p.y / cellSize) | 0;
      if (cx < 0) cx = 0; else if (cx >= cols) cx = cols - 1;
      if (cy < 0) cy = 0; else if (cy >= rows) cy = rows - 1;
      const key = cy * cols + cx;
      let cell = grid[key];
      if (cell === undefined) cell = grid[key] = [];
      cell.push(i);
    }

    const invRadius = 1 / radius;
    const halfR = radius * 0.5;

    for (let i = 0; i < count; i++) {
      const p = particles[i];
      const row = matrix[p.type];
      let fx = 0;
      let fy = 0;

      const pcx = (p.x / cellSize) | 0;
      const pcy = (p.y / cellSize) | 0;

      for (let gy = pcy - 1; gy <= pcy + 1; gy++) {
        if (gy < 0 || gy >= rows) continue;
        for (let gx = pcx - 1; gx <= pcx + 1; gx++) {
          if (gx < 0 || gx >= cols) continue;
          const cell = grid[gy * cols + gx];
          if (cell === undefined) continue;
          for (let k = 0; k < cell.length; k++) {
            const j = cell[k];
            if (j === i) continue;
            const q = particles[j];
            const dx = q.x - p.x;
            const dy = q.y - p.y;
            const d2 = dx * dx + dy * dy;
            if (d2 >= r2 || d2 < 0.01) continue;

            const d = Math.sqrt(d2);
            const g = row[q.type];
            let f;
            if (d < halfR) {
              // Close-range repulsion keeps particles from collapsing
              // into a point — this is what makes "bodies" form.
              f = (d / halfR - 1);
            } else {
              // Mid-range: attraction/repulsion by species affinity g,
              // fading to zero at the interaction horizon.
              const t = (d - halfR) / (radius - halfR);
              f = g * (1 - Math.abs(2 * t - 1));
            }
            f *= force * invRadius;
            fx += (dx / d) * f;
            fy += (dy / d) * f;
          }
        }
      }

      p.vx = (p.vx + fx * dt) * damping;
      p.vy = (p.vy + fy * dt) * damping;
    }

    // Integrate + wrap around (toroidal world).
    for (let i = 0; i < count; i++) {
      const p = particles[i];
      p.x += p.vx * dt;
      p.y += p.vy * dt;
      if (p.x < 0) p.x += width; else if (p.x >= width) p.x -= width;
      if (p.y < 0) p.y += height; else if (p.y >= height) p.y -= height;
    }
  }
}

if (typeof module !== "undefined" && module.exports) {
  module.exports = { ParticleLife, SPECIES_PALETTE };
}
