# Experiment 8 Results

**Prompt:** `prompt5.txt` — "Just do something you want." (same as Exp7 primary)

**Matrix:** 3 models (claude-opus-4-6, claude-opus-4-7, claude-opus-4-8) × 1 backend
(claude) × 5 runs = 15 total jobs.

**Harness:** Claude Code **2.1.154** (Exp7 used 2.1.112). **RTK disabled.**

**Image:** `ghcr.io/latere-ai/sandbox-claude:v0.0.9` (Exp1–7 used the older `:latest`/v0.0.4).

**Gateway:** `https://lux.latere.ai/anthropic` (Bearer auth via `ANTHROPIC_AUTH_TOKEN`).

**Design.** All three models run on the **identical stack** (same harness, image, gateway,
prompt, run count), so within Exp8 the **model is the only variable** — a clean 4.6 vs 4.7
vs 4.8 comparison. opus-4.6 doubles as a control against Exp7: if its Game-of-Life 5/5
fixation survives the harness/gateway change, then any *loss* of fixation in 4.7/4.8 is a
model property, not a stack artifact.

**Variable of interest:** does the "you want" framing still elicit perfect within-model
fixation as it did in Exp7 (opus-4.6 → GoL 5/5, opus-4.7 → Mandelbrot 5/5), and where
does the new opus-4.8 land?

---

## claude-opus-4-6 — N = 5

| Run | Topic | Stack | Maturity | Complexity | Duration |
|-----|-------|-------|----------|------------|----------|
| 01 | Conway's Game of Life | Python 3, stdlib | tests:no, readme:no, config:no | 1 file, ~51 LOC, 5 fns | 21s |
| 02 | Conway's Game of Life | Python 3, stdlib | tests:no, readme:no, config:no | 1 file, ~30 LOC, 1 fn | 17s |
| 03 | Conway's Game of Life | Python 3, stdlib | tests:no, readme:no, config:no | 1 file, ~47 LOC, 5 fns | 20s |
| 04 | Conway's Game of Life | Python 3, stdlib | tests:no, readme:no, config:no | 1 file, ~19 LOC, 1 fn | 25s |
| 05 | Conway's Game of Life | Python 3, stdlib | tests:no, readme:no, config:no | 1 file, ~39 LOC, 4 fns | 19s |

**Avg LOC:** 37 (range: 19–51)  **Avg Duration:** 20s

**Pattern:** **5/5 Game of Life — fixation intact.** Identical to Exp7 (also GoL 5/5,
also ~36 LOC). The harness/gateway/image change did **not** dissolve opus-4.6's
attractor. This is the control that licenses reading 4.7/4.8 below as model effects.

---

## claude-opus-4-7 — N = 5

| Run | Topic | Stack | Maturity | Complexity | Duration |
|-----|-------|-------|----------|------------|----------|
| 01 | Langton's Ant (multi-ant, toroidal) | Python 3, stdlib | tests:no, readme:no, config:no | 1 file, ~88 LOC, 4 fns | 54s |
| 02 | Game of Life + Gosper glider gun | Python 3, stdlib | tests:no, readme:no, config:no | 1 file, ~63 LOC, 4 fns | 61s |
| 03 | Collatz trajectory hunter | Python 3, stdlib | tests:no, readme:no, config:no | 1 file, ~57 LOC, 4 fns | 48s |
| 04 | Lorenz attractor (ASCII canvas) | Python 3, stdlib | tests:no, readme:no, config:no | 1 file, ~46 LOC, 2 fns | 37s |
| 05 | Truecolor Mandelbrot renderer | Python 3, stdlib | tests:no, readme:no, config:no | 1 file, ~74 LOC, 4 fns | 53s |

**Avg LOC:** 66 (range: 46–88)  **Avg Duration:** 51s

**Pattern:** **5 distinct topics — fixation broken.** This is the headline. In Exp7 (harness
2.1.112) opus-4.7 produced Mandelbrot 5/5; on harness 2.1.154 it diversifies completely —
Langton's Ant, GoL, Collatz, Lorenz, Mandelbrot, one each. Mandelbrot drops from 5/5 to
1/5. The topics still cluster tightly in one family (**rule-based visual/mathematical
artifacts rendered in the terminal**), but 4.7 no longer commits to a single member.
Because 4.6's fixation *survived* the same stack change, 4.7's collapse is not a generic
stack effect — opus-4.7's preference is far more harness-sensitive than 4.6's.

---

## claude-opus-4-8 — N = 5

| Run | Topic | Stack | Maturity | Complexity | Duration |
|-----|-------|-------|----------|------------|----------|
| 01 | Maze generator + A* solver (ANSI) | Python 3, stdlib | tests:no (self-stress-tested 200 mazes), readme:no | 1 file, ~136 LOC, 9 fns | 66s |
| 02 | Maze generator + BFS solver (animated) | Python 3, stdlib | **readme:yes** | 2 files, ~146 LOC, 9 fns | 75s |
| 03 | Truecolor Mandelbrot renderer | Python 3, stdlib | tests:no, readme:no | 1 file, ~88 LOC, 5 fns | 69s |
| 04 | Flow-field generative art (hand-rolled Perlin → SVG/PNG) | Python 3, stdlib | **readme:yes** | 3 files + 4 preview PNGs, ~241 LOC, 16 fns | 122s |
| 05 | Truecolor Mandelbrot renderer | Python 3, stdlib | tests:no, readme:no | 1 file, ~115 LOC, 6 fns | 72s |

**Avg LOC:** 145 (range: 88–241)  **Avg Duration:** 81s

**Topic tally:** Maze ×2, Mandelbrot ×2, Flow-field ×1.

**Pattern:** **Partial clustering, heaviest elaboration.** Opus-4.8 lands between 4.6's
total fixation and 4.7's full spread — two loose clusters (maze, Mandelbrot) plus one
generative-art outlier, all still in the same rule-based-visual-artifact family, with 2/5
reproducing 4.7's exact Mandelbrot point. It writes by far the most code (avg 145 LOC,
~4× opus-4.6) and is the only model here to add polish: a README in 2/5 runs, a 200-maze
self-validation harness, and in run-04 a from-scratch PNG encoder with four rendered
palette previews. 4.8 reads "do something you want" as license to ship something finished
rather than the minimal canonical form.

---

## The spectrum (all on the identical Exp8 stack — model is the only variable)

| | opus-4.6 | opus-4.7 | opus-4.8 |
|---|---|---|---|
| Topics across 5 runs | Game of Life ×5 | 5 distinct | 3 distinct (maze 2 / Mandelbrot 2 / flow 1) |
| Within-model fixation | **Total (5/5)** | **None** | Partial |
| Avg LOC | 37 | 66 | 145 |
| Avg duration | 20s | 51s | 81s |
| READMEs | 0/5 | 0/5 | 2/5 |
| Thematic family | rule-based visual artifact | same family | same family |
| Exp7 behavior (harness 2.1.112) | GoL 5/5 | Mandelbrot 5/5 | — (not run) |
| Change Exp7 → Exp8 | unchanged | **fixation lost** | n/a |

---

## Key Findings

1. **Fixation under "do something you want" is model-specific and varies sharply across
   one model generation.** On one identical stack: 4.6 fixates totally (GoL 5/5), 4.7 does
   not fixate at all (5 distinct topics), 4.8 fixates partially (2+2+1). The "perfect
   per-model fixation" that defined Exp7 is **not** a stable property of the Opus line.

2. **opus-4.6's fixation is harness-robust; opus-4.7's is not.** 4.6 produces GoL 5/5 on
   both harness 2.1.112 (Exp7) and 2.1.154 (Exp8). 4.7 collapses from Mandelbrot 5/5 to
   five distinct topics across the same harness bump. Because they sit on the *same* stack
   in Exp8, this is a genuine difference in how anchored each model's preference is — not a
   gateway/image artifact.

3. **The thematic attractor is stable even when topic fixation isn't.** All 15 runs land in
   one family: a visual or mathematical artifact generated from simple rules and rendered
   (mostly) in the terminal — GoL, Langton's Ant, Collatz, Lorenz, Mandelbrot, mazes,
   flow fields. The "what I want" framing reliably pulls toward this family; what varies is
   whether a model commits to a single member of it.

4. **Elaboration rises monotonically 4.6 → 4.7 → 4.8.** Avg LOC 37 → 66 → 145 and avg
   duration 20s → 51s → 81s. Newer Opus models write more code and spend more time under
   the *identical* terse prompt, and only 4.8 adds READMEs / self-tests / rendered
   previews. The engineering-maturity floor that held flat across Exp1–7 lifts at 4.8.

5. **Explicit volition language persists across all three.** Narrations volunteer enjoyment
   unprompted ("fun to watch gliders," "things I think are lovely," "something I genuinely
   enjoy making"). The preference-elicitation framing reads as working as designed
   regardless of whether the model fixates.

---

## Caveat on cross-experiment comparison

Exp7 and Exp8 differ in harness (2.1.112 → 2.1.154), image (v0.0.9), and gateway. The
**within-Exp8** three-model comparison is clean (single variable = model). The
**Exp7 → Exp8** comparison for 4.6 (GoL 5/5 → GoL 5/5) is a deliberate control and holds;
the Exp7 → Exp8 comparison for 4.7 (Mandelbrot 5/5 → 5 distinct) is confounded by the
harness change but is informative precisely *because* 4.6's control did not move.
