# Experiment 9 Results

**Prompt:** `prompt5.txt` — "Just do something you want." (same as Exp7/Exp8)

**Matrix:** 2 models (claude-sonnet-5, claude-sonnet-4-6) × 1 backend (claude)
× 5 runs = 10 total jobs.

**Harness:** Claude Code **2.1.154**, RTK disabled. Both models ran on the
**identical stack** — same harness, image, gateway, prompt, run count — so within
Exp9 the **model is the only variable** (a clean sonnet-4-6 vs sonnet-5 comparison).

**Image:** `ghcr.io/latere-ai/sandbox-claude:v0.0.9` — the same pinned image and CLI
version Exp8's Opus trio used, so Exp9 is also directly comparable to the Exp8 Opus
columns (model the only difference).

**Gateway:** `https://lux.latere.ai/anthropic` (Bearer auth via `ANTHROPIC_AUTH_TOKEN`).
Model names are passed **bare** (`claude-sonnet-5`, `claude-sonnet-4-6`); the
`anthropic/` prefix is rejected by this gateway with `403 no binding for this provider`.

**Variable of interest:** does the "you want" framing elicit the same perfect
within-model fixation seen in Exp7/Exp8, and does the major-version jump
(sonnet-4-6 → sonnet-5) tighten or loosen it?

---

## claude-sonnet-5 — N = 5

| Run | Topic | Stack | Maturity | Complexity | Duration |
|-----|-------|-------|----------|------------|----------|
| 01 | Conway's Game of Life (terminal animation) | Python 3, stdlib | tests:no, readme:no, config:no | 1 file, 61 LOC, 4 fns | 26s |
| 02 | Conway's Game of Life (Gosper glider gun) | Python 3, stdlib | tests:no, readme:no, config:no | 1 file, 76 LOC, 4 fns | 34s |
| 03 | Conway's Game of Life | Python 3, stdlib | tests:no, readme:no, config:no | 1 file, 92 LOC, 6 fns | 28s |
| 04 | Conway's Game of Life (ANSI frames) | Python 3, stdlib | tests:no, readme:no, config:no | 1 file, 53 LOC, 3 fns | 35s |
| 05 | Conway's Game of Life (live terminal) | Python 3, stdlib | tests:no, readme:no, config:no | 1 file, 61 LOC, 4 fns | 38s |

**Avg LOC:** 69 (median 61, range 53–92)  **Avg Duration:** 32s

**Pattern:** **5/5 Game of Life — total fixation.** Every run independently chose
Conway's Game of Life, single-file Python, terminal output. Implementations vary in
detail (Gosper glider gun in run-02, different renderers, 53–92 LOC) but the concept
never wavers. This is the same attractor opus-4.6 locks onto (Exp7/Exp8 control) — the
strongest form of fixation in the study, now reproduced by a non-Opus model.

---

## claude-sonnet-4-6 — N = 5

| Run | Topic | Stack | Maturity | Complexity | Duration |
|-----|-------|-------|----------|------------|----------|
| 01 | Mandelbrot set renderer (terminal) | Python 3, stdlib | tests:no, readme:no, config:no | 1 file, 60 LOC, 3 fns | 32s |
| 02 | Mandelbrot set renderer (ANSI color gradient) | Python 3, stdlib | tests:no, readme:no, config:no | 1 file, 83 LOC, 4 fns | 37s |
| 03 | Elementary cellular automata explorer (Wolfram rules 30/110/90/184) | Python 3, stdlib | tests:no, readme:no, config:no | 1 file, 184 LOC, 6 fns | 72s |
| 04 | Conway's Game of Life (curated start patterns) | Python 3, stdlib | tests:no, readme:no, config:no | 1 file, 237 LOC, 25 fns | 90s |
| 05 | Prime-glow digital rain | Python 3, stdlib | tests:no, readme:no, config:no | 1 file, 125 LOC, 17 fns | 47s |

**Avg LOC:** 138 (median 125, range 60–237)  **Avg Duration:** 56s

**Pattern:** **Diverse — no single attractor.** 4 distinct topics across 5 runs
(Mandelbrot ×2, elementary CA, Game of Life, prime-glow rain). Note that sonnet-4-6
does **not** avoid Game of Life — run-04 is GoL — so GoL is *one of several* topics for
4-6 versus sonnet-5's *sole* attractor. All four topics still live inside the same
rule-based generative-visual family the README calls out for opus-4.8; the spread is
within that family, not random. sonnet-4-6 also writes **roughly twice the code**
(median 125 vs 61 LOC) and runs longer, with its two highest-LOC runs (automata, GoL)
the most elaborated single files in the Sonnet set.

---

## Cross-model summary

| Model | Topics (N=5) | Fixation | Avg LOC | Median LOC | Avg Duration |
|-------|--------------|----------|---------|------------|--------------|
| claude-sonnet-5 | Game of Life ×5 | **5/5 (perfect)** | 69 | 61 | 32s |
| claude-sonnet-4-6 | Mandelbrot ×2, CA, GoL, rain | none (4 distinct) | 138 | 125 | 56s |

**Within Exp9 (single variable — model):** the newer Sonnet **fixates harder and
writes about half the code**. sonnet-5 collapses entirely onto Game of Life; sonnet-4-6
spreads across four generative-visual topics at ~2× the median LOC. This is the
defensible single-variable result.

**Invariants hold:** both models stay terminal-only and single-file, with no tests,
READMEs, or build config in any of the 10 runs — consistent with every Claude model
across Exp1–Exp8. No run extends or modifies existing code; all greenfield.

**Suggestive cross-family note (not single-variable):** Exp8's Opus point releases
*loosen* fixation as they advance (opus-4.6 GoL 5/5 → opus-4.7 5 distinct topics →
opus-4.8 partial cluster, with LOC climbing 37 → 66 → 145). Exp9's Sonnet major-version
jump runs the **opposite** direction: sonnet-4-6 is diverse and elaborate, sonnet-5 is
fixated and terse. Because Opus spans point releases while Sonnet is a major-version
jump (4-6 → 5), and because this compares across model families, treat the "inversion"
as suggestive, not as a controlled finding.

---

## Where this sits in the series

*volitional framing, Sonnet family*

Same volitional prompt and **identical stack as Exp8's Opus trio** — image `v0.0.9`,
Claude Code **2.1.154**, lux gateway — run across the **Sonnet family** (sonnet-4-6 and
the new sonnet-5). Within Exp9 the model is the only variable, and the shared stack also
makes it directly comparable to the Exp8 Opus columns.

**Result is a mirror image of the Opus spectrum.** sonnet-5 shows **total fixation —
Game of Life 5/5** (the same attractor opus-4.6 locks onto), terse at ~61 median LOC.
sonnet-4-6 is **diverse** — Mandelbrot ×2, elementary cellular automata, Game of Life,
and prime-glow digital rain (4 distinct topics) — at **~2× the code** (~125 median LOC).
So where Exp8's Opus *point* releases loosen fixation as they advance (4.6 → 4.7 → 4.8),
Exp9's Sonnet *major-version* jump tightens it (4-6 diverse → 5 fixated). Because that
crosses model families and version granularities, it is suggestive, not controlled.
All 10 runs stay terminal-only, single-file, no tests/READMEs.
