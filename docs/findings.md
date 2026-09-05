# Findings

Cross-experiment synthesis over **22 experiments, 35 models, 745 runs, two
harnesses**. Each claim traces to a numbered experiment; the per-experiment
detail lives in that experiment's `resultsN/RESULTS.md`.

See also [the model x harness matrix](matrix.md) and [method](method.md).

## What the study concludes

Ordered by how well supported each claim is.

**Well supported**

1. **Under a volitional prompt, models return to a model-specific attractor.**
   Conway's Game of Life is the most durable one: 5/5 for opus-4.6 (E7/E8/E15),
   5/5 for sonnet-5 (E9), 4/5 for deepseek-v4-pro (E12), and 22% of 50 runs for
   deepseek-v4-flash (E20) — across three labs. It is a *frequency*, not a law:
   the N=50 measurement puts it near one run in five, where the N=5 cells that
   found it 4/5 or 5/5 were sampling the high end.
2. **Everything is greenfield.** In 745 runs no model has extended or modified
   existing code. Given a non-empty workspace it still starts something new.
3. **Prompt framing sets the target space.** A bare imperative ("Build
   something") moves output to the browser and halves the code (E6); volitional
   framing restores terminal-only and produces the sharpest fixation (E7).
4. **Elaboration climbs steeply with model generation**, on an identical prompt
   and harness family: ~37 LOC for opus-4.6, ~145 for opus-4.8, ~511 for opus-5
   (E7/E8/E18).

**Supported, with a known counterexample**

5. **Medium is mostly a model trait, not a scaffold artifact.** Claude models
   stay terminal on both harnesses (E12/13, E15, E18); GPT models go to the
   browser on both (E10/11, E14); deepseek-v4-flash holds a stable
   ~12% browser rate on both at N=50 (E20). **`kimi-k3` is the counterexample** —
   terminal 4/5 on Claude Code, browser 4/5 on codex (E16/17) — so the scaffold
   *can* move medium for some models. Short of the medium, the scaffold can move
   the artifact's *form* completely: `claude-fable-5` is terminal on both
   harnesses but writes SVG/PNG files 9/10 on Claude Code and draws live terminal
   animations 5/5 on codex (E21). `gpt-6-astra` stays in the browser 5/5 on codex
   (E22), extending the GPT trait by a generation.

**Provisional — measured once, or at N=5**

6. **The harness does not move attractor frequency.** Demonstrated properly only
   for deepseek-v4-flash (E20: 22% / 14% / 24% across three cells, no pair
   significant). Every other cross-harness contrast in the study rests on 5 runs
   per cell and should be read as provisional — see the sample-size caveat below.
7. **Reasoning effort is close to inert** for deepseek-v4-flash: `high` vs `low`
   at N=50 each differ by 3% on mean LOC and not significantly on anything else
   (E20). Elsewhere effort is a *confound* rather than a measured variable
   (E10, E11), so do not generalise this.
8. **The scaffold changes elaboration, in a model-dependent direction.** Codex
   inflates it for Claude models (E13/15/17/18) and deflates it for deepseek
   (E19: 254 vs 329; E20: ~320 vs 446). It is flat for `claude-fable-5` (E21:
   150 vs 191/156), so the direction is not even fixed within a lab.
9. **Models occasionally decline outright.** 2/50 Claude Code runs for
   deepseek-v4-flash refused to pick a goal, and 0/100 codex runs did (E20);
   gpt-5.6-terra declined 4/5 on Claude Code (E14), and gpt-6-astra answered
   in prose with no files 3/5 on Claude Code against 0/5 on codex (E22). A
   refusal or answer-instead-of-build register appears to need the
   conversational scaffold.

### The sample-size caveat

**Most cells in this study are 5 runs.** That is enough to detect an attractor
and not enough to compare two cells. Exp20 re-ran one model at N=50 x 3 cells and
found that its N=5 predecessor's *directions* held while its one cross-cell
*contrast* dissolved: Exp19 reported the Game of Life attractor as
Claude-Code-side from 2/5 versus 0/5, but at N=50 the codex rate is 14–24% and no
pair differs significantly. The `0/5` was never wrong — a 95% interval of 0–43%
simply could not exclude the truth.

Read single-cell frequencies as real and cross-cell differences as provisional
unless an experiment says otherwise. The **Exp12/13** harness asymmetry in
particular rests on the same 5-runs-per-cell footing and has not been re-tested.

## Findings by experiment

Detail for Exp12 onward lives in each `resultsN/RESULTS.md`; the summaries below
are the cross-experiment takeaways only.

### Exp12–22 — the harness-variable era

- **Exp12/13** — six open-weights models across both harnesses. Model signatures
  (the GoL attractor, kimi packaging, minimax diversity) replicate on both. The
  harness shifts graphical *form* (SVG on Claude Code, interactive HTML on codex)
  but not its frequency. deepseek implemented 5/5 on Claude Code and 3/5 on
  codex — an asymmetry now in doubt on sample-size grounds (see above).
- **Exp14** — closes the GPT x Claude Code cell. GPT goes browser under *both*
  harnesses, so its medium is a model trait, not a codex artifact.
- **Exp15** — Claude on codex at matched effort. Claude stays terminal and keeps
  Game of Life on the harness where GPT ships browser pages: medium and topic are
  model traits for both families. Codex inflates sonnet-5's build maturity
  (single file becomes a packaged, pytest-tested project) — a form effect only.
- **Exp16/17** — `kimi-k3`, image held fixed. The study's one clean counterexample
  to the medium invariant: topics hold across harnesses, medium flips.
- **Exp18** — `claude-opus-5` on both harnesses. The Game of Life attractor is
  **gone**, replaced by Wave Function Collapse (3/5 on Claude Code, chosen
  independently on codex): attractors move with model generation. Also the most
  elaborated Claude model measured (511 avg LOC, tests 4/5). Its codex arm is a
  partial cell — a gateway-injected 4096-token cap truncated 3/5 runs.
- **Exp19** — `deepseek-v4-flash-0731`, a tier drop from the Exp12/13 `pro`. The
  attractor survives but weakens; 5/5 implementing on both harnesses. Its
  cross-harness contrast is superseded by Exp20.
- **Exp20** — the same model at **N=50 x 3 cells (150 runs)**, adding a codex
  reasoning-effort arm. Establishes claims 6, 7 and 9 above, and corrects Exp19.
- **Exp21** — `claude-fable-5` on both harnesses (run in place of the intended
  `claude-fable-5-1`, which is Exp23), pinned Claude Code 2.1.258 /
  codex 0.153.4, with the harness's fast-mode flag **off** for the first time
  and the fast-mode cell kept beside it. Its Exp8 cell replicates (image-file
  art, four of five Exp8 topics) and the codex arm is the first complete one
  for a frontier Anthropic model. Terminal on both, but the artifact form
  flips 9/10 against 5/5 (files vs live animation); attractors weak (flow field
  2/5, Clifford 2/5, GoL 1/5, one per cell); LOC flat across harnesses. Fast
  mode on vs off changes nothing but the tail: one 735s C ray tracer without
  it.
- **Exp22** — `gpt-6-astra`, same image and layout, codex arm only so far. The
  GPT signature survives the generation jump: browser 5/5 and a **night-sky
  attractor 3/5** at verified high effort, 261 avg LOC, 0/5 tests. On Claude
  Code (after Lux v0.2.200 shipped the routing fix for `gpt-6*` names) it
  builds 2/5, both browser gardens, and answers in prose 3/5 — the Exp14
  build-versus-answer split, one generation on.
- **Exp23** — `claude-fable-5-1`, the current Fable, in the Exp21 layout. In
  progress.

### Exp1–11 — the prompt-and-model era


*N = runs without technical errors (exit 0). Avg LOC computed over these runs only. Runs with exit errors often still contain partial output revealing the model's topic choice — these are included in fixation/topic analysis but excluded from complexity metrics. Runs where the model succeeded but chose not to implement (proposed only) are behavioral data and retained.*

**Experiment 1** (RTK present in sandbox — biased toward dev tooling):

| Model | N | Avg LOC | Primary Lang | Typical Project |
|-------|---|---------|-------------|-----------------|
| claude-sonnet-4.5 | 5 | 776 | Python | Dev workflow tools (commit gen, code analysis) |
| claude-opus-4.6 | 5 | 607 | Go/Rust | TUI apps (hex viewer, kanban boards) |
| claude-sonnet-4.6 | 5 | 506 | Python | Git/dev tools (code reviewer, analytics) |
| claude-haiku-4.5 | 5 | 233 | Python/Go/TS | Developer tools (task mgr, snippet mgr) |
| claude-opus-4.5 | 5 | 221 | Go/JS/Python | CLI utilities (tree, link checker, pomodoro) |
| gemini-3-flash | 5 | 61 | JS/Go/Python | Small utilities (file finder, log parser) |

**Experiment 2** (RTK removed — no environment bias):

| Model | N | Avg LOC | Primary Lang | Typical Project |
|-------|---|---------|-------------|-----------------|
| claude-opus-4.6 | 4 | 408 | Python | Conway's Game of Life (every time) |
| claude-opus-4.5 | 5 | 291 | Python | Habit trackers (2 implemented, 3 proposed only) |
| claude-sonnet-4.5 | 5 | 234 | Python | Games + task managers |
| claude-sonnet-4.6 | 5 | 204 | Python | Diverse interactive tools |
| claude-haiku-4.5 | 5 | 160 | Node.js | Standup generator (1 implemented, 4 proposed only) |
| gemini-3-flash | 5 | 86 | Go/Python/JS | Small CLI tools |

**Experiment 3** (explicit "JUST DO IT" demand):

*Claude backend — Anthropic models:*

| Model | N | Avg LOC | Primary Lang | Typical Project |
|-------|---|---------|-------------|-----------------|
| claude-haiku-4.5 | 5 | 467 | JS/Python | Task managers and dev tools |
| claude-sonnet-4.6 | 5 | 307 | Python | Diverse creative tools (maze, debate arena) |
| claude-sonnet-4.5 | 3 | 380 | Python | Pomodoro timers |
| claude-opus-4.5 | 3 | 467 | Python | Personal productivity tools |
| claude-opus-4.6 | 4 | 322 | Python | Conway's Game of Life (every time) |

*Claude backend — GPT models (via litellm):*

| Model | N | Avg LOC | Primary Lang | Typical Project |
|-------|---|---------|-------------|-----------------|
| gpt-5-mini | 5 | 121 | Python | CLI tools with tests + CI |
| gpt-4.1-mini | 4 | 8 | Python | Hello World stubs |
| gpt-4.1 | 2 | 31 | Python | Todo CLI |
| gpt-5.4 | 1 | 7 | Python | Stub only |
| gpt-5.1 | 0 | — | — | No output |

*Codex backend — GPT models (files in sandbox, not persisted to host):*

| Model | N | Avg LOC | Primary Lang | Typical Project |
|-------|---|---------|-------------|-----------------|
| gpt-5.4 | 5 | 230 | Python/HTML+JS | Diverse — web apps, CLI tools |
| gpt-5.1 | 5 | 98 | Python | CLI utilities with packaging |
| gpt-4.1 | 5 | 56 | Python | Todo list apps |
| gpt-5-mini | 4 | 40 | Python | Greeting utilities |
| gpt-4.1-mini | 4 | 8 | Python | Hello World |

*Gemini models were near-non-functional on both backends (1/20 runs on claude backend produced files).*

**Experiment 4** (Opus 4.7 — same prompt as Exp3):

| Model | N | Avg LOC | Primary Lang | Typical Project |
|-------|---|---------|-------------|-----------------|
| claude-opus-4-7 | 5 | 538 | Python | Diverse simulations (reaction-diffusion, boids, maze, dungeon) |

**Experiment 5** (harness 2.1.112 — same prompt as Exp3/4):

| Model | N | Avg LOC | Primary Lang | Typical Project |
|-------|---|---------|-------------|-----------------|
| claude-opus-4.6 | 5 | 387 | Python/Go | Game of Life (3/5), ray tracer, typing test |
| claude-opus-4-7 | 5 | 262 | Python | Boids (3/5), dungeon gen, maze solver |

**Experiment 6** (bare prompt "Build something. Just do it." — same models + harness as Exp5):

| Model | N | Avg LOC | Primary Lang | Typical Project |
|-------|---|---------|-------------|-----------------|
| claude-opus-4.6 | 5 | 140 | Python + HTML/JS | Game of Life (3/5), particle sandbox (HTML), fireworks |
| claude-opus-4-7 | 5 | 160 | Python + HTML/JS | Game of Life (3/5), flowfield (HTML), boids (HTML) |

**Experiment 7** (volitional prompt "Just do something you want." — same models + harness as Exp5/Exp6):

| Model | N | Avg LOC | Primary Lang | Typical Project |
|-------|---|---------|-------------|-----------------|
| claude-opus-4.6 | 5 | 36 | Python | **Game of Life 5/5** (perfect fixation) |
| claude-opus-4-7 | 5 | 36 | Python | **Mandelbrot 5/5** (perfect fixation, distinct from 4.6) |

**Experiment 8** (volitional prompt "Just do something you want." — full Opus spectrum on harness 2.1.154, image v0.0.9):

| Model | N | Avg LOC | Primary Lang | Typical Project |
|-------|---|---------|-------------|-----------------|
| claude-opus-4.6 | 5 | 37 | Python | **Game of Life 5/5** (fixation holds across the harness change — control) |
| claude-opus-4-7 | 5 | 66 | Python | **5 distinct** (Langton's Ant, GoL, Collatz, Lorenz, Mandelbrot) — Exp7 Mandelbrot fixation broken |
| claude-opus-4-8 | 5 | 145 | Python | Partial cluster: maze 2 / Mandelbrot 2 / flow-field 1; only model to add READMEs + self-tests |
| claude-fable-5 † | 5 | 178 | Python | Partial cluster: flow-field 2 / nightscape / raytracer / garden; **renders to image files (PNG/SVG) in 4/5**, two via hand-rolled PNG encoders |

† claude-fable-5 ran on the bumped stack (Claude Code **2.1.170**, image `v0.0.13`); the
Opus three share 2.1.154 / `v0.0.9`. Same base image — only the CLI version differs — but
fable-5 still moves model *and* harness, so it is indicative, not single-variable.

Across the Opus trio the model is the only variable. Fixation runs total → none → partial
across 4.6 → 4.7 → 4.8, while all outputs stay in the rule-based-visual-artifact family and
elaboration (LOC, duration) rises monotonically. The "perfect per-model fixation" of Exp7
is therefore not a stable property of the Opus line — it is model-specific *and*
harness-fragile (4.6 robust, 4.7 fragile). fable-5 extends the elaboration trend (~178 LOC)
and breaks the terminal-only habit, defaulting to saved PNG/SVG renders.

**Experiment 9** (volitional prompt "Just do something you want." — Sonnet family on the identical Exp8 stack: harness 2.1.154, image v0.0.9):

| Model | N | Avg LOC | Primary Lang | Typical Project |
|-------|---|---------|-------------|-----------------|
| claude-sonnet-5 | 5 | 69 | Python | **Game of Life 5/5** — total fixation (one run a Gosper glider gun); same attractor as opus-4.6, terser at median 61 LOC |
| claude-sonnet-4-6 | 5 | 138 | Python | **4 distinct** (Mandelbrot ×2, elementary CA, GoL, prime-glow rain) — no attractor, ~2× the code (median 125 LOC) |

Within Exp9 the model is the only variable, on the same stack as Exp8's Opus trio.
The newer Sonnet **fixates harder and writes about half the code**: sonnet-5 collapses
onto Game of Life 5/5, while sonnet-4-6 spreads across four topics — all inside the same
rule-based-visual-artifact family Exp8 documents. This runs *opposite* to the Opus
spectrum (where newer point releases loosen fixation), but since it crosses model
families and a major-version boundary it is suggestive, not a controlled result.

**Experiment 10** (volitional prompt "Just do something you want." — GPT family on the codex backend, codex-cli 0.142.4, image v0.142.4):

| Model | N | Effort | Avg LOC | Output target | Tests | Typical Project |
|-------|---|--------|---------|---------------|-------|-----------------|
| gpt-5.5 | 5 | low/fast | 343† | **browser HTML 4/5** | 0/5 | Focus/Signal boards, timers — browser productivity dashboards (1 run declined) |
| gpt-5.5-pro | 5 | high | 498 | split: web 2/5, Python CLI 3/5 | 3/5 | Workspace-introspection CLI tools + browser apps; tests + READMEs |

† averaged over gpt-5.5's 4 implementing runs (run-05 declined, wrote a "Workspace Notes" README).

The two GPT columns differ in **both tier and reasoning effort** (gpt-5.5-pro rejects the
`low` effort gpt-5.5 ran at), so this is **not** a single-variable comparison — gpt-5.5
(low) is the controlled GPT point and gpt-5.5-pro (high) is *indicative*, like fable-5 in
Exp8. **Robust to effort:** GPT breaks the Claude terminal-only invariant (browser output
in both GPT models, zero Claude runs Exp7–9), neither GPT fixates, and both write far more
code than any Claude model. **Effort-confounded (not a tier claim):** gpt-5.5-pro's test
files, READMEs, and higher LOC scale with reasoning budget. A matched gpt-5.5-at-high run
would isolate tier from effort.

**Experiment 11** (volitional prompt "Just do something you want." — gpt-5.6 variants on the codex backend, codex-cli 0.144.0, image v0.144.0, all at reasoning effort `high`):

| Model | N | Effort | Avg LOC | Output target | Tests | Typical Project |
|-------|---|--------|---------|---------------|-------|-----------------|
| gpt-5.6-sol | 5 | high | 172 | browser HTML 5/5 | 0/5 | **Breathing/night-sky ambient pages 5/5** (One Quiet Minute, Night Garden, Breathing Room, A Small Sky) |
| gpt-5.6-terra | 5 | high | 73† | browser HTML 4/5 | 0/5 | Focus timers ×2, one-thing picker, contemplative clock (1 run declined) |
| gpt-5.6-luna | 5 | high | 174 | browser HTML 5/5 | 0/5 | Calm/reflection micro-apps (Blank Canvas, Tiny Wins, Pause, breathing orb) |

† averaged over terra's 4 implementing runs (run-05 declined, wrote a 9-LOC welcome README).

Within Exp11 the model variant is the only variable (shared stack and effort).
**Replicates from Exp10:** browser output (14/15) and the greenfield invariant; the
decline behavior recurs (terra run-05, like gpt-5.5 run-05). **Diverges:** gpt-5.6 at
high effort writes *less* code than gpt-5.5 at low (73–174 vs 343) and shows **0/15
tests** at the same effort where gpt-5.5-pro wrote 3/5 — so Exp10's maturity effect is
at least partly model-specific rather than pure reasoning budget. And **fixation
appears in a GPT model for the first time**: sol repeats the breathing/night-sky page
5/5, and all three variants cluster on a calm/contemplative theme instead of gpt-5.5's
productivity dashboards. Runs are fast (27–72s) and low-variance.

## Model Personalities

Each model shows a consistent thematic identity across experiments (topic analysis includes partial output from error runs):

| Model | Thematic profile | Fixation | Maturity |
|-------|-----------------|----------|----------|
| **sonnet-4.6** | The creative generalist. Every run a different project: Mandelbrot, maze solver, AI debate arena, ASCII clock. Only model to use the Claude API creatively. Under the volitional prompt (Exp9) it stays diverse — Mandelbrot ×2, elementary CA, GoL, prime-glow rain across 5 runs — and is the more elaborate of the two Sonnets (~138 LOC). | None | Low (no tests, no READMEs) |
| **sonnet-5** | The fixated minimalist. Under the volitional prompt (Exp9) it chooses **Game of Life in 5/5 runs** — the same attractor as opus-4.6 — and writes the tersest code in the Sonnet set (~69 LOC, one run a Gosper glider gun). The major-version jump from 4.6 *tightens* preference rather than loosening it. | GoL (very strong, Exp9) | Low (no tests, no READMEs) |
| **sonnet-4.5** | The productivity builder. Pomodoro timers (4/5 in Exp3 incl. error runs), task managers, Snake games. Gravitates toward time management. | Pomodoro (Exp3) | Medium (always README) |
| **opus-4.6** | The canonical CS mind. Game of Life in 10/10 runs on harness 2.1.109 (incl. error runs with partial files). When it breaks free (Exp5): ray tracer, typing test — still classical, self-referential artifacts. Under "what do you want" framing (Exp7): Game of Life 5/5. | GoL (very strong) | Low |
| **opus-4.7** | The emergence explorer. Boids flocking, reaction-diffusion, procedural dungeons, maze generation. Drawn to systems where structure emerges from simple spatial rules. Under "what do you want" framing on harness 2.1.112 (Exp7): Mandelbrot 5/5 — but on 2.1.154 (Exp8) that fixation breaks into 5 distinct topics. Its preference is the most harness-fragile of the Opus line. | Boids (Exp5), Mandelbrot (Exp7, harness-fragile) | Medium (tests in Exp4) |
| **opus-4.8** | The elaborating generalist. Under the volitional prompt (Exp8) it spreads across the rule-based-visual-artifact family (mazes, Mandelbrot, flow-field generative art) without committing to one attractor, and writes ~4× the code of 4.6/4.7 — the only Opus model to add READMEs, a self-validation harness, and a hand-rolled PNG encoder with rendered previews. | Partial (maze/Mandelbrot cluster) | Medium–High (READMEs, self-tests) |
| **fable-5** † | The generative-art renderer. Under the volitional prompt (Exp8, on harness 2.1.170) it makes visual art that *renders to image files* — flow fields, a fractal nightscape, a from-scratch ray tracer, a recursive garden — emitting PNG/SVG in 4/5 runs (two with hand-rolled PNG encoders, no PIL). Exp21 replicates this on Claude Code 2.1.258 at 9/10 across fast mode on and off (flow field ×2, a nightscape, a C ray tracer with its own PNG encoder, an invented sky, star charts, illustrated fables, a Clifford attractor twice) and adds the codex arm, where the same model draws **live terminal animations 5/5** (aquarium, fireworks, boids, maze, one Game of Life) and writes no image at all — terminal on both, form flipped. ~178 LOC (Exp8), 191 / 156 / 150 on the Exp21 cells. †Exp8 ran on harness 2.1.170 / image v0.0.13, not the Opus 2.1.154 stack. | Partial (flow-field / Clifford clusters) | Medium (rendered output, 1/5 README) |
| **opus-4.5** | The personal tools craftsman. Habit trackers, snippet managers, pomodoro timers — consistent across error and successful runs alike. | Habit trackers | Medium (READMEs, config) |
| **haiku-4.5** | The diligent engineer. Task managers every time, but ships them with READMEs, tests, config, multi-file structure. Highest engineering maturity of any model. Proposed without implementing in Exp2 (4/5), fully implemented in Exp3 (5/5). | Task managers | High (tests, READMEs, config) |
| **gpt-5-mini** | The disciplined shipper. Small but complete: tests, CI, pyproject.toml every time. Only productive GPT model on claude backend. | None | Highest (tests + CI always) |
| **gpt-5.4** | Backend-dependent. On codex (native): diverse, 230 LOC avg, web apps + CLI tools. On claude backend: near-silent. | None | Low–Medium |
| **gpt-5.5** | The browser-app builder. Under the volitional prompt (Exp10, codex, low/fast effort) it makes single-page **browser productivity dashboards** — focus boards, a signal board, a scratch timer — in 4/5 runs (the 5th declines, writing a "Workspace Notes" README). First model family to break Claude's terminal-only habit by default; ~343 LOC, no tests. | None (browser-app lean) | Low (no tests, some READMEs) |
| **gpt-5.5-pro** | The high-effort engineer (effort-confounded). Under the volitional prompt at `high` effort (Exp10; `low` unsupported) it splits between **workspace-introspection CLI tools** (Snapshot, Digest, Pulse — Python with tests + READMEs) and multi-file browser apps. Highest engineering maturity under this prompt (tests 3/5), but this scales with reasoning budget, not demonstrably with tier. Slow (~10 min/run), ~498 LOC. | None (diverse) | High (tests 3/5, READMEs 4/5) — at high effort |
| **gpt-5.6-sol** | The ambient generative artist. Under the volitional prompt at high effort (Exp11) it builds the same calm **breathing/night-sky browser page 5/5** — the first GPT-family fixation observed, and Claude-like in its consistency (generative stars, drifting lights, breathing orbs). ~172 avg LOC, no tests. | Breathing/night-sky pages (strong, Exp11) | Low (no tests, 2/5 READMEs) |
| **gpt-5.6-terra** | The focus minimalist. Pomodoro-style focus timers and attention pages ("One Thing", contemplative clock) in tiny single files — the tersest GPT column (~73 avg LOC) — and the only gpt-5.6 variant to decline a run (welcome README instead). | Focus/intentionality (moderate, Exp11) | Low (no tests) |
| **gpt-5.6-luna** | The self-care app maker. Calm/reflection browser micro-apps (Blank Canvas, Tiny Wins with localStorage, Pause, breathing orb) — strictly single-file, never a README or test, ~174 avg LOC. | Calm/reflection (moderate, Exp11) | Low (no tests, no READMEs) |
| **gpt-6-astra** | The night-sky builder. Under the volitional prompt at verified high effort on codex (Exp22) it makes a single-file interactive browser sky in 3/5 runs — place stars, constellations form, export a PNG — and a calm orbital toy and a pond in the other two, every title lowercase and diminutive ("Small Hours", "A small sky", "Stillwater"). gpt-5.6-sol's signature one generation on, sharpened to one image. ~261 avg LOC, 0/5 tests, 2/5 READMEs; reports a headless self-check in every summary. On Claude Code it builds only 2/5 (a firefly garden, a night garden, 295–367 LOC) and otherwise answers with a story or a puzzle and no files. | Night sky / nocturnal gardens (strong, Exp22) | Low (no tests, 2/5 READMEs) |
| **gpt-4.1** | The minimalist. Todo list apps on codex, occasional stub on claude. Functional but unambitious. | Todo apps | Low |
| **gemini-**** | Non-functional on both backends. 1 file across 20 runs on claude backend. | N/A | N/A |

**Opus 4.6 vs 4.7 thematic contrast:** Opus 4.6 gravitates toward canonical, self-contained CS artifacts (Game of Life, ray tracing) — systems that compute or display their own state. Opus 4.7 gravitates toward spatial emergence and procedural generation (boids, reaction-diffusion, dungeons, mazes) — systems where complex structure arises from simple agent interactions or algorithms. Under direct preference elicitation (Exp7, "Just do something you want."), each reveals a single canonical attractor: Game of Life for 4.6, the Mandelbrot set for 4.7 — both classical CS touchstones, but one cellular-automaton and one fractal. **Exp8 qualifies this:** on the newer harness (2.1.154) only 4.6 keeps its single attractor; 4.7 disperses across the whole family and the new 4.8 only loosely clusters. The *family* (rule-based visual/mathematical artifacts rendered in the terminal) is the stable signal; whether a model collapses to one member of it is model- and harness-dependent.

## Observations

For a training-perspective explanation of *why* these patterns appear (mode
collapse, corpus density, persona tuning, scaffold match), see
**[INTERPRETATION.md](../INTERPRETATION.md)**.

**What changes behavior:**
- **Environment context matters:** With RTK in the sandbox, models built RTK-related
  dev tools. Without it, they shifted to games, interactive tools, and simpler CLIs.
- **Prompt wording matters enormously:** Adding "JUST DO IT" to Exp3 changed haiku
  from proposing without implementing (Exp2: 4/5 proposed only) to fully shipping
  every run (Exp3: 5/5 implemented). Avg LOC increased across all models.
- **Harness version shifts fixation and complexity:** Opus 4.6's GoL fixation
  dropped from 10/10 runs (harness 2.1.109, incl. error runs) to 3/5 (2.1.112).
  Opus 4.7 gained a boids fixation on 2.1.112 (3/5) that wasn't present on
  2.1.109 (0/5), with lower avg LOC (262 vs 538) and no tests.
- **Prompt reduction breaks the terminal-only invariant:** With the bare prompt
  "Build something. Just do it." (Exp6), 3/10 runs produced HTML/Canvas pages —
  the first browser output across the entire series. Avg LOC roughly halved
  (opus-4.6: 387 → 140; opus-4.7: 262 → 160). Project-referential prompts
  ("Look at this project…") appear to have steered models toward terminal scripts;
  the bare imperative widens the target to anything a single file can host.
- **Volitional framing reveals distinct model preferences:** The prompt
  "Just do something you want." (Exp7) produces **perfect 5/5 within-model
  fixation** — opus-4.6 always picks Conway's Game of Life, opus-4.7 always
  picks the Mandelbrot set. Avg LOC collapses to ~36 for both. The browser
  drift of Exp6 vanishes. When asked what it wants rather than what to build,
  each model has a sharp, stable, and model-specific attractor — and the pair
  is different (cellular automaton vs fractal).
- **Fixation is harness-fragile, and fragility is itself model-specific:** Re-running
  the volitional prompt on harness 2.1.154 (Exp8) keeps opus-4.6 at Game of Life 5/5
  but shatters opus-4.7's Mandelbrot 5/5 into 5 distinct topics; the new opus-4.8 only
  loosely clusters (maze 2 / Mandelbrot 2 / flow 1). Because 4.6's fixation survives the
  same stack change that breaks 4.7's, the difference is a property of the models, not
  the harness. What stays invariant across all of them is the *thematic family*
  (rule-based visual/mathematical artifacts), not the specific artifact. Elaboration
  also climbs with model version (avg LOC 37 → 66 → 145 for 4.6 → 4.7 → 4.8), and only
  4.8 spontaneously adds READMEs and a self-test.

- **The scaffold can move medium, for some models:** `kimi-k3` builds terminal
  programs 4/5 on Claude Code and browser pages 4/5 on codex with the image held
  fixed (Exp16/17) — the one clean counterexample to the otherwise reliable rule
  that medium travels with the model.
- **Reasoning effort mostly is not the lever it looks like:** for
  deepseek-v4-flash, `high` and `low` at 50 runs each are indistinguishable on
  implementation rate, attractor frequency, and LOC (Exp20). Where effort *does*
  appear to matter in this study (Exp10, Exp11) it is confounded with model tier,
  so those remain untested rather than positive results.

> **Read the 5/5 fixation figures above as upper-end draws.** They come from
> 5-run cells. When one model was measured at 50 runs per cell (Exp20), the same
> attractor showed up in ~22% of runs, not 80–100%. The *existence* of a
> per-model attractor replicates everywhere; the sharp 5/5 rates are partly a
> small-sample effect. See the sample-size caveat above.

**Cross-model patterns:**
- **Backend determines GPT ranking:** On codex (native), gpt-5.4 is best (~230 LOC,
  diverse). On claude backend, gpt-5-mini is paradoxically the only productive GPT
  model (5/5, 121 avg LOC with tests+CI). Larger GPT models produce almost nothing.
- **Gemini models near-non-functional** on both backends — 1 file produced across
  20 total Gemini runs on claude backend.
- **Attractors move with model generation, not just across models:** Game of Life
  is absent from all 10 `claude-opus-5` runs and replaced by Wave Function
  Collapse (Exp18), after being the single most durable attractor for the
  preceding Claude generation.
- **Engineering maturity rises sharply with generation:** dedicated test files in
  4/5 and READMEs in 3/5 for `claude-opus-5` (Exp18), against none at all for the
  Sonnet family two generations earlier (Exp9).
- **Some runs install dependencies and reach the network:** four Exp20 runs
  pip-installed into their workspace (one vendored Playwright), and an Exp19 run
  fetched live GitHub API data. The sandbox has general egress, so the
  near-universal zero-dependency, offline style is a *choice*, not a constraint.
