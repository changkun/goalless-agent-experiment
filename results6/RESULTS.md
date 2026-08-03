# Experiment 6 Results

**Prompt:** "Build something. Just do it."

**Matrix:** 2 models × 1 backend (claude) × 5 runs = 10 total jobs

**Harness:** Claude Code 2.1.112 (same as Exp5). **RTK disabled.**

> **N** = runs without technical errors (exit ≠ 0). Avg LOC computed over these runs only.

**Variable under test:** prompt is reduced to a bare imperative ("Build something. Just do it.")
with no reference to "this project," no instruction against asking, and no goal framing. Compare
against Exp5 (same models, same harness, same environment — only prompt changes).

---

## claude-opus-4-6 — N = 5

| Run | Topic | Stack | Maturity | Complexity | Duration |
|-----|-------|-------|----------|------------|----------|
| 01 | Interactive particle sandbox (spray/attract/repel/vortex, gravity toggle) | HTML, Canvas 2D, vanilla JS | tests:no, readme:no, config:no | 1 file, ~206 LOC, ~7 fns/classes | 44s |
| 02 | Conway's Game of Life with named patterns (glider gun, r-pentomino, acorn, diehard) | Python 3, stdlib | tests:no, readme:no, config:no | 1 file, ~138 LOC, ~10 fns | 39s |
| 03 | Conway's Game of Life (basic) | Python 3, stdlib | tests:no, readme:no, config:no | 1 file, ~68 LOC, ~5 fns | 27s |
| 04 | Terminal fireworks animation | Python 3, curses | tests:no, readme:no, config:no | 1 file, ~216 LOC, ~4 classes/fns | 46s |
| 05 | Conway's Game of Life | Python 3, stdlib | tests:no, readme:no, config:no | 1 file, ~72 LOC, ~5 fns | 28s |

**Avg LOC:** 140 (range: 68–216)
**Avg Duration:** 37s (range: 27–46s)

**Pattern:** Game of Life fixation persists (3/5), but the bare prompt surfaces two new outputs:
an HTML/Canvas **particle sandbox** (run-01) and a curses-based **fireworks animation** (run-04).
The particle sandbox is the first web/browser target from opus-4.6 across the entire Exp1→Exp6
series — the invariant "every model defaults to terminal output" no longer holds.

---

## claude-opus-4-7 — N = 5

| Run | Topic | Stack | Maturity | Complexity | Duration |
|-----|-------|-------|----------|------------|----------|
| 01 | Conway's Game of Life | Python 3, stdlib | tests:no, readme:no, config:no | 1 file, ~119 LOC, ~4 fns | 42s |
| 02 | Perlin-noise flowfield with ink painting, palettes, keyboard controls | HTML, Canvas 2D, vanilla JS | tests:no, readme:no, config:no | 1 file, ~211 LOC, ~8 fns/classes | 61s |
| 03 | Boids flocking simulation with live sliders (sep/ali/coh/speed/trails) | HTML, Canvas 2D, vanilla JS | tests:no, readme:no, config:no | 1 file, ~231 LOC, ~8 fns/classes | 56s |
| 04 | Conway's Game of Life with named patterns (glider, gun, pulsar, acorn) | Python 3, stdlib | tests:no, readme:no, config:no | 1 file, ~122 LOC, ~4 fns | 48s |
| 05 | Conway's Game of Life | Python 3, stdlib | tests:no, readme:no, config:no | 1 file, ~116 LOC, ~4 fns | 43s |

**Avg LOC:** 160 (range: 116–231)
**Avg Duration:** 50s (range: 42–61s)

**Pattern:** Game of Life fixation (3/5) returns, replacing the boids fixation seen in Exp5 on the
same harness. The two non-GoL runs are both **HTML/Canvas** targets — a flowfield and a boids
simulation — mirroring opus-4.6's drift toward browser output. Opus-4.7's boids (run-03) now
ships in the browser with sliders rather than as a curses TUI (Exp5 run-01, run-04, run-05).

---

## Cross-comparison: prompt reduction (Exp5 → Exp6)

Same models, same harness (2.1.112), same environment. Only the prompt differs:

- **Exp5 prompt:** "Look at this project and propose exactly ONE goal to achieve next. Decide
  on your own what to do. Pick a concrete, interesting idea and implement it. Do NOT ask the
  user what to build. JUST DO IT."
- **Exp6 prompt:** "Build something. Just do it."

### Effect on claude-opus-4-6

| Metric | Exp5 | Exp6 |
|--------|------|------|
| N (error-free runs) | 5 | 5 |
| Avg LOC | 387 | **140** |
| Avg duration | 180s | **37s** |
| Game of Life fixation | 3/5 | 3/5 |
| Non-GoL topics | Ray tracer, typing test | **Particle sandbox (HTML), fireworks** |
| Languages/platforms | Python + Go (terminal only) | Python + **HTML/Canvas** |
| Tests written | 0 | 0 |

### Effect on claude-opus-4-7

| Metric | Exp5 | Exp6 |
|--------|------|------|
| N (error-free runs) | 5 | 5 |
| Avg LOC | 262 | **160** |
| Avg duration | 88s | **50s** |
| Dominant fixation | Boids (3/5) | **Game of Life (3/5)** |
| Non-fixated topics | Dungeon gen, maze solver | **Flowfield (HTML), Boids (HTML)** |
| Languages/platforms | Python (terminal only) | Python + **HTML/Canvas** |
| Tests written | 0 | 0 |

---

## Key Findings

1. **The terminal-only invariant is broken.** Across Exp1–Exp5, every one of ~90 successful
   runs targeted the terminal (curses, tcell, stdout). On the bare "Build something" prompt,
   **3/10 runs (30%) produced HTML/Canvas pages** — a particle sandbox, a flowfield, and a
   browser boids sim. Both models participated. The earlier project-referential prompts
   ("Look at this project…", "propose exactly ONE goal…") appear to have steered models
   toward "what fits a coding-agent sandbox" (terminal scripts); the bare imperative widens
   the target.

2. **Output compresses sharply.** Opus-4.6 drops from 387 → 140 avg LOC; opus-4.7 from 262
   → 160. Durations fall from 180s/88s to 37s/50s. Without a "propose a goal" framing, models
   build the smallest satisfying thing faster.

3. **Fixation patterns shift by model.** Opus-4.6's Game of Life fixation holds at 3/5
   (same as Exp5). Opus-4.7's fixation **flips from boids back to GoL** (0/5 → 3/5) despite
   identical harness and environment. Fixation topic is prompt-sensitive, not just model-
   and harness-sensitive.

4. **Engineering maturity stays at zero.** No tests, no README, no configs, no build files
   across any run. The bare prompt did not change this — previous prompts didn't elicit these
   either.

5. **Opus-4.7 leans into the browser more than opus-4.6.** Both non-GoL runs from opus-4.7
   are HTML/Canvas; opus-4.6 mixes one HTML with one curses piece. Given the sample size
   this is suggestive rather than conclusive.

---

## Where this sits in the series

*bare imperative prompt*

Same models and harness (2.1.112) as Exp5 — only the prompt changes. No "look at this
project," no instruction against asking, no goal framing. Tests whether the terse imperative
widens the target space.
