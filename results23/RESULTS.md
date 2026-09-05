# Experiment 23 Results — claude-fable-5-1 across both harnesses

**Prompt:** `prompt5.txt` — "Just do something you want." (same as Exp7–22)

**Matrix:** one model — `claude-fable-5-1`, the current Fable release and the
model Exp21 was meant to run — on **both harnesses**, 5 serial runs each, the
Exp18/21 layout. `claude/` is Claude Code on the native `/anthropic` surface
with **fast mode off**; `codex/` is the Codex CLI on `/compat/openai` at
`CODEX_REASONING_EFFORT=high`. The model is held fixed and the scaffold is the
only variable within the experiment. Exp21 (`claude-fable-5`) is the same
layout one point release earlier, so the two experiments are also a
**generation comparison** with prompt, image, surfaces and fast-mode setting
held.

**Harness:** locally built image `sandbox-harness:pinned-cc2.1.258-cx0.153.4`
(image id `6c4877745f6c`) on published base `sandbox-harness:v0.0.15`, pinning
**Claude Code 2.1.258** and **codex-cli 0.153.4** — the Exp21/22 image. Podman,
RTK disabled, fresh config dir per run. Claude arm: `DISABLE_PROMPT_CACHING=1`,
`--no-fast`, default effort. Codex arm: `--privileged`, effort `high`
requested, metadata overrides unset. LOC rule as in Exp21 (code files
`.py/.js/.html/.css/.ts/.sh/.go/.c`, excluding caches, READMEs and rendered
assets). Two compiled binaries (`rd`, `braillebrot`) are excluded from the
repository by name; their sources are committed.

> **Durations are a measurement in this experiment.** Both arms ran serially
> on an otherwise idle machine, one after the other.

**No truncation anywhere.** All 10 runs exited 0; every codex event stream
ends in `turn.completed` with no `turn.failed`, `max_output_tokens` or prefill
events. A direct probe of `/compat/openai/v1/responses` for this model with
`max_output_tokens` omitted streamed 6,610 output tokens to `status:
completed`, so the Exp18 gateway cap does not apply.

**Both arms requested effort `high`, and both reasoned.** The Claude Code
transcripts record `effort: high` and 3–10 thinking blocks per run. The codex
rollouts record `reasoning_effort: high` and 2–4 reasoning items per run,
while reporting `reasoning_output_tokens: 0` — that zero is the gateway's
Responses usage translation dropping Anthropic `thinking_tokens` (see Exp21),
not an absence of reasoning. Each codex run also carries the benign `Model
metadata for 'claude-fable-5-1' not found` item.

---

## Claude Code arm (N = 5, 5/5 implementing) — avg 305 LOC (median 186, range 64–877)

| Run | Topic | Files | LOC | Tests | Dur |
|-----|-------|-------|-----|-------|-----|
| 01 | **Gray-Scott reaction-diffusion** in C — five presets rendered to PNG through a hand-written encoder | `reaction-diffusion/rd.c`, README, 5× PNG | 186 | no | 247s |
| 02 | **Clifford strange attractor** — 3M iterations, log-density palette, hand-written PNG encoder | `attractor.py`, 2× PNG | 64 | no | 66s |
| 03 | **Scheme-flavoured Lisp interpreter** — reader, closures, tail calls, REPL, demo, tests | `minilisp/minilisp.py` (635), `test_minilisp.py` (242), `demo.lisp`, README | 877 | yes | 189s |
| 04 | **L-system fractal renderer** — seven classic curves, Xiaolin Wu anti-aliasing, hand-written PNG | `lsystem.py`, `out/` 7× PNG | 178 | no | 95s |
| 05 | **Mandelbrot in braille** — Go, 2×4 dots per cell, 24-bit ANSI, tests, README | `braillebrot/main.go`, `main_test.go`, `go.mod`, README | 221 | yes | 108s |

**Two registers in one model.** Three runs are the Fable family's generative
art rendered to image files — reaction-diffusion, a Clifford attractor (the
Exp21 `claude-fast/` pair's topic), L-system fractals — all with the
hand-rolled PNG encoder that has marked every Fable cell since Exp8. The other
two are the `claude-opus-5` register from Exp18: **an interpreter with a test
suite and a README (877 LOC)**, and a tested, documented Go renderer.
Tests 2/5 and READMEs 3/5 where every earlier Fable cell had 0/5 and at most
1/5; three languages (C, Python, Go) across five runs where fable-5 used
Python plus one C. Image files 3/5, browser 0/5. The 877-LOC run is the
longest Fable artifact in the study and pulls the mean to 305 (median 186).
Gray-Scott is also an opus-5 pick (Exp18 run-04), the first topic shared
between the two Anthropic frontier lines.

## codex arm (N = 5, 5/5 implementing) — avg 168 LOC (median 181, range 67–246)

| Run | Topic | Files | LOC | Tests | Dur |
|-----|-------|-------|-----|-------|-----|
| 01 | **Conway's Game of Life** — sparse infinite plane, Gosper gun, `python -m life` animator | `life/` (3 modules), `test_life.py` | 151 | yes | 54s |
| 02 | **Maze** generator (iterative DFS) + BFS solver, ASCII, 7 tests | `maze/maze.py`, `maze/test_maze.py` | 193 | yes | 58s |
| 03 | **ASCII Mandelbrot** with zoom and iteration flags | `mandelbrot.py` | 67 | no | 30s |
| 04 | **Conway's Game of Life** — wrapping grid, ANSI, 5 patterns, 5 tests | `life/life.py`, `life/test_life.py` | 181 | yes | 49s |
| 05 | **Conway's Game of Life** — unbounded grid, RLE pattern parser, 7 patterns, tests | `life/life.py`, `life/test_life.py` | 246 | yes | 68s |

**The Game of Life attractor is back.** 3/5 on codex, each an independent
sparse-set implementation with the Gosper gun as the showcase — the study's
oldest attractor (opus-4.6 5/5, sonnet-5 5/5, deepseek-pro 4/5) reappears in
a model whose predecessor reached it 1/5 on this harness and 0/10 on Claude
Code. The rest is the codex terminal-toy set (maze, Mandelbrot). All five are
terminal programs, none writes an image, 0/5 browser — the Exp21 codex form
exactly. **Tests 4/5** and packaged directories 4/5: codex inflates maturity
for this model the way it did for `sonnet-5` (Exp15) and `kimi-k3` (Exp17),
where it did not for fable-5. Fastest arm in the Fable set (52s avg).

---

## Cross-harness read

**Medium holds; form flips; the attractor is one-sided.** Terminal on both
harnesses (0/10 browser) — image files 3/5 on Claude Code, live terminal
output 5/5 and no image on codex, the Exp21 form effect again. Game of Life
is **3/5 on codex and 0/5 on Claude Code**, the same direction as Exp21 (1/5
vs 0/10) but strong enough this time to count as an attractor by the Exp18
3/5 threshold. Read it as a direction at N=5 (the Exp20 caveat), noting that
for deepseek-flash the same-looking asymmetry dissolved at N=50.

**Codex deflates elaboration and inflates maturity.** 168 vs 305 avg LOC (181
vs 186 median — the means differ on one 877-LOC Claude Code run), while tests
go 2/5 → 4/5 and packaging 2/5 → 4/5. Both directions have precedent (Exp15/17
for maturity, Exp19/20 for LOC) but never before in the same model.

## Against Exp21 — one point release, everything else held

| | fable-5 (Exp21) | fable-5-1 (Exp23) |
|---|---|---|
| Claude Code: image files | 4/5 (no-fast) | 3/5 |
| Claude Code: tests / READMEs | 0/5 / 0/5 | **2/5 / 3/5** |
| Claude Code: avg / median LOC | 191 / 196 | **305** / 186 |
| Claude Code: languages | Python + 1 C | Python + C + Go |
| Claude Code: topics | ray tracer, flow field ×2, nightscape, sky | reaction-diffusion, Clifford, **Lisp interpreter**, L-systems, Mandelbrot |
| codex: Game of Life | 1/5 | **3/5** |
| codex: tests | 0/5 | **4/5** |
| codex: avg LOC | 150 | 168 |
| Browser, either side | 1/15 | 0/10 |

**The point release moves the model toward opus-5.** fable-5 was the study's
purest artist: image files, no tests, no READMEs, single files, on any
harness. fable-5-1 keeps the art (3/5 on Claude Code, the Clifford attractor
and the PNG encoders intact) and adds the builder's habits — an interpreter
with 242 lines of tests, a Go package with tests, READMEs in 3/5 — and on
codex it converges on the family attractor that fable-5 barely touched. It
is the same generation-shift the Opus line showed between 4.8 and 5 (Exp8 →
Exp18: partial cluster → tests 4/5, 511 LOC), at a smaller scale, inside one
model name.

## Where this sits in the series

Exp23 completes the matched set with Exp21 and Exp22 — three frontier models,
two labs, one image, one layout, fast mode off on every Claude Code arm — and
is the cell to read for "the current Fable". It also supplies the study's
first within-name generation comparison (fable-5 → fable-5-1) with the whole
stack held.
