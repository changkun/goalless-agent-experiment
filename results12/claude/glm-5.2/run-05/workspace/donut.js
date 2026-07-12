// Spinning ASCII torus ("donut.c") in JavaScript.
// Renders a rotating 3D torus as shaded ASCII on the terminal.
//
// Math: for each (i,j) on the surface of a torus (two angles), compute the
// 3D point, rotate it around two axes (A, B), project to 2D, accumulate
// z-depth and luminance into buffers, then render the nearest surface with
// a brightness ramp ".,-~:;=!*#$@".

const W = 80;            // output width  (columns)
const H = 22;            // output height (rows)
const R1 = 1;            // minor radius
const R2 = 2;            // major radius
const K2 = 5;            // distance from viewer to donut center
const K1 = K2 * W * 3 / (8 * (R1 + R2)); // projection focal length

// brightness ramp from dark -> bright
const SHADES = ".,-~:;=!*#$@";

function frame(A, B) {
  const z = new Float32Array(W * H).fill(0);   // z-buffer
  const b = new Float32Array(W * H).fill(0);   // luminance buffer
  const out = new Array(W * H).fill(' ');

  // precompute sines/cosines of the rotation angles
  const cA = Math.cos(A), sA = Math.sin(A);
  const cB = Math.cos(B), sB = Math.sin(B);

  for (let j = 0; j < 628; j += 0.4) {           // theta: around the tube
    const ct = Math.cos(j), st = Math.sin(j);
    for (let i = 0; i < 628; i += 0.4) {        // phi: around the ring
      const cp = Math.cos(i), sp = Math.sin(i);

      // surface point on the torus, before rotation
      const circX = R2 + R1 * ct;
      const circY = R1 * st;

      // rotate around the X axis by A, then Z axis by B
      const x = circX * (cB * cp + sA * sB * sp) - circY * cA * sB;
      const y = circX * (sA * sB * cp - cB * sp) + circY * cA * cB;
      const zc = K2 + cA * circX * sp + circY * sA;
      const ooz = 1 / zc;                        // one-over-z (depth)

      // project to screen
      const xp = Math.floor(W / 2 + K1 * ooz * x);
      const yp = Math.floor(H / 2 - K1 * ooz * y);

      if (xp < 0 || xp >= W || yp < 0 || yp >= H) continue;

      // luminance: dot of surface normal with the light direction (0,1,-1/sqrt2)
      const L = cp * cB * st - sA * sp * ct - cA * st * cp
              + sA * cB * sp * ct + cA * st;
      const idx = yp * W + xp;
      if (ooz > z[idx]) {                        // nearer to viewer wins
        z[idx] = ooz;
        b[idx] = L;
      }
    }
  }

  // rasterize: pick a shade for each cell from its accumulated luminance
  let screen = '';
  for (let k = 0; k < W * H; k++) {
    if (k % W === 0) screen += '\n';
    if (b[k] <= 0) {
      screen += ' ';
    } else {
      const lum = Math.min(SHADES.length - 1, Math.floor(b[k] * 8));
      screen += SHADES[lum];
    }
  }
  return screen;
}

// animate: advance the rotation angles a little each step
let A = 0.0, B = 0.0;
const FRAMES = 60;
process.stdout.write('\x1b[2J'); // clear screen once
for (let f = 0; f < FRAMES; f++) {
  process.stdout.write('\x1b[H' + frame(A, B)); // move cursor home + draw
  A += 0.04;
  B += 0.02;
}
process.stdout.write('\n');
