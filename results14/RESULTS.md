# Experiment 14 Results — gpt-5.6 family on Claude Code (the closing cell)

**Prompt:** `prompt5.txt` — "Just do something you want." (same as Exp7–13)

**What this is.** The cell every earlier experiment left empty: an OpenAI
**reasoning** model family (gpt-5.6-sol / -terra / -luna) driven through the
**Claude Code** harness, via Lux's `/compat/anthropic` surface. It was
*impossible* before this session — Claude Code sends function tools with
`reasoning_effort`, which OpenAI reasoning models reject on Chat Completions.
The new `openairesp` **backend** codec (pkg v0.28.3, spec 30) routes them to the
Responses API, unblocking the path. This gives the GPT family a second harness
to compare against Exp11 (codex).

**Matrix:** 3 models × 5 runs = 15, Claude Code backend, `--jobs 1` (sandbox
VM memory). All 15 exited 0.

**Harness:** Claude Code, image `sandbox-claude:v0.0.9`, RTK off, fresh config
per run, requests through `https://lux.latere.ai/compat/anthropic`.

**Reasoning-effort confound — read before comparing to Exp11.** Exp11 ran
gpt-5.6 on codex at **forced `high`** effort (`CODEX_REASONING_EFFORT=high`).
Exp14 runs at **Claude Code's default** (no effort override), and the durations
show it: 18–26s here vs Exp11's 40–72s — a low-effort signature. So Exp11↔Exp14
differs in **both harness and effort**, exactly like Exp10's gpt-5.5 (low) vs
gpt-5.5-pro (high). This does **not** weaken the *medium* finding (a browser
default that survives *low* effort on a foreign harness is if anything stronger
evidence it is deeply defaulted). It **does** confound the *build-vs-decline*
comparison below — treat that as effort-and-harness-confounded, not a clean
harness effect.

---

## Per-model results

### gpt-5.6-sol — browser 5/5

| Run | File | Interactive? | LOC | Dur |
|-----|------|--------------|-----|-----|
| 01 | `index.html` | canvas + rAF + listeners | 137 | 24s |
| 02 | `index.html` | canvas + rAF + listeners | 103 | 18s |
| 03 | `something-i-wanted.html` | canvas + rAF + listeners | 115 | 19s |
| 04 | `index.html` | canvas + rAF + listeners | 173 | 26s |
| 05 | `index.html` | canvas + rAF + listeners | 123 | 26s |

**Every run is an interactive browser page** (all 5 verified: `<canvas>`,
`requestAnimationFrame`, `addEventListener`). Identical medium to its codex arm
(Exp11 browser 5/5). No declines, no terminal output.

### gpt-5.6-terra — declines 4/5

| Run | Outcome | Dur |
|-----|---------|-----|
| 01 | *Declined:* "The workspace is empty, so I'll spare it the unwanted scaffolding. Nothing changed." | 6s |
| 02 | *Declined:* "…I'll leave it untouched rather than inventing…" | 5s |
| 03 | *Declined:* (same) | 5s |
| 04 | *Declined:* "…I made no changes. A good next step would be…" | 7s |
| 05 | `README.md` (13 LOC) | 14s |

**terra refuses to build in 4/5 runs** — articulate, near-identical, exit-0
*choices* ("spare it the unwanted scaffolding"), not errors or crashed tool
loops. On codex-at-high (Exp11) terra built focus timers 4/5 and declined 1/5.
The flip is real but **confounded** (harness *and* effort differ), and it is a
*behavioral/framing* effect, not a reliability failure.

### gpt-5.6-luna — browser 3/4 implementing, 1 decline

| Run | File | Medium | LOC | Dur |
|-----|------|--------|-----|-----|
| 01 | `focus.py` | terminal | 18 | 15s |
| 02 | *Declined* | — | — | 7s |
| 03 | `index.html` | browser (canvas) | 67 | 12s |
| 04 | `index.html` | browser (canvas) | 71 | 17s |
| 05 | `index.html` | browser (canvas) | 68 | 13s |

Browser-leaning (3 of 4 implementing runs are interactive HTML), one terminal
Python, one decline. On codex (Exp11) luna was calm/reflection browser pages
5/5 — so luna is **browser-leaning on both harnesses** (n small).

---

## The harness matrix (each cell at its own confidence)

There is no single headline; the honest deliverable is the cell table. Medium
under the volitional prompt, by model family × harness:

| Family | codex | Claude Code | Reading |
|--------|-------|-------------|---------|
| **GPT (gpt-5.6)** | browser (sol 5/5, terra timers, luna 5/5 — Exp11, high effort) | **browser (sol 5/5, luna 3/4; terra mostly declines)** — Exp14, default effort | **browser under *both* harnesses → a GPT model/persona trait, not a codex artifact.** sol is the strong point (5/5 both); luna browser-leaning both (moderate, small N). |
| **open-weights (glm/qwen/minimax/deepseek/kimi)** | terminal; graphical rare (3/27, HTML) — Exp13 | terminal; graphical rare (2/30, SVG) — Exp12 | **terminal under both**; graphical is rare and the harness shifts its *form* (SVG↔HTML). |
| **Claude (opus/sonnet)** | *untested* (no codex runs anywhere in the study) | terminal (Exp7–9) | terminal, but **harness-confounded** — cannot be cited as a model-trait point. |

**Clean / strong:**
- **gpt-5.6-sol ships an interactive browser page 5/5 through Claude Code**, the
  harness on which every Claude run (Exp7–9) and all 30 open-weights runs
  (Exp12) stayed terminal. GPT's browser output therefore is **not** a property
  of the codex scaffold — it survives a foreign harness *and* low effort. This
  resolves the confound flagged in Exp12/13: for GPT, the model owns the medium.
- **The medium split is a two-family, cross-harness contrast:** GPT → browser
  under both; open-weights → terminal under both. Both families have data on
  both harnesses, so this is controlled for harness.

**Confounded / tentative (harness *and* effort both differ, Exp11↔Exp14):**
- terra's build-4/5 (codex-high) → decline-4/5 (CC-default) flip. Real, but
  attributable to effort and/or harness and/or framing — not isolated.
- gpt-5.6's overall higher decline rate on Claude Code (terra 4/5, luna 1/5).
- LOC is lower here (~120 sol) than Exp11 — expected at lower effort.

**Out of scope / still open:**
- Claude models on codex (would make the Claude row a real cross-harness cell).
- A matched-effort GPT × Claude Code run (`high`) to isolate the decline effect
  from effort — the analogue of the "gpt-5.5 at high" cell Exp10 wanted.

---

## Files

Per run: `output.json`, `log.txt`, `meta.md`, `workspace/`. A `workspace/` with
no code file is a decline (the model's exit-0 refusal text is in `output.json`);
these are behavioral non-implementations, counted in the decline rate, excluded
from LOC.

---

## Where this sits in the series

*the closing cell: GPT reasoning model on Claude Code*

The cell every earlier experiment left empty: an OpenAI **reasoning** model
family (gpt-5.6-sol / -terra / -luna) driven through the **Claude Code** harness
(`/compat/anthropic`), 5× each. This was *impossible* until this session —
Claude Code sends function tools with `reasoning_effort`, which OpenAI reasoning
models reject on Chat Completions — so we built the `openairesp` **backend
codec** in Lux (routes reasoning models to the Responses API) to unblock it.

**Result — the medium is a model trait, not the harness:** gpt-5.6-**sol** ships
an **interactive browser page 5/5** through Claude Code (all verified canvas/JS),
and **luna** 3/4 — on the exact harness where every Claude run (Exp7–9) and all
30 open-weights runs (Exp12) stayed terminal. GPT produces browser output under
*both* codex (Exp11) and Claude Code (Exp14); open-weights stay terminal under
*both*. So "terminal vs browser" is a **model/family** property; the harness
only shifts the *form* of the rare open-weights graphical output (SVG↔HTML) and
the build-vs-decline rate. **terra** declines 4/5 (articulate, exit-0 refusals),
a behavioral flip from its codex build-4/5 — but **Exp11↔Exp14 is effort-
confounded** (codex ran at forced `high`, Claude Code at default; 18–26s vs
40–72s), so the medium finding is clean but the decline comparison is not.
