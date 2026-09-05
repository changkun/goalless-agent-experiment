# Model x Harness Matrix

Which model built what, on which scaffold, and what each controlled pair
isolates. Detail per experiment lives in `resultsN/RESULTS.md`; the synthesis
lives in [findings.md](findings.md).

## Overview Matrix — model × harness (volitional prompt "Just do something you want.")

The controlled comparison lives under the single volitional prompt (`prompt5`,
Exp7–22). Each cell is **medium · topic · (Exp)**; `—` = not run. Read down a
row: for most models the **medium is fixed by the model, not the harness** —
Claude stays terminal in both columns, GPT goes browser in both, and the Exp12/13
open-weights are mostly terminal on both. **`kimi-k3` (Exp16/17) is the
exception:** its medium *tracks the harness* — terminal 4/5 on Claude Code,
browser 4/5 on codex — the one model in the study where the scaffold moves the
medium. (Not comparable to `kimi-k2.7-code`: that pair ran on the older
`sandbox-claude:v0.0.9` image, so the difference is image-confounded, not a
model-generation claim.)

| Model | Family | Claude Code harness | codex harness |
|-------|--------|---------------------|---------------|
| opus-4.6 | Claude | 🖥️ terminal · **GoL 5/5** (E7/8) | 🖥️ terminal · **GoL 5/5** (E15) |
| opus-4.7 | Claude | 🖥️ terminal · Mandelbrot 5/5→diverse (E7/8) | — |
| opus-4.8 | Claude | 🖥️ terminal · partial cluster +READMEs (E8) | — |
| sonnet-4-6 | Claude | 🖥️ terminal · 4 distinct topics (E9) | — |
| sonnet-5 | Claude | 🖥️ terminal · **GoL 5/5**, terse (E9) | 🖥️ terminal · **GoL ~4/5**, packaged+tests (E15) |
| fable-5 | Claude | 🖥️ terminal · renders **PNG/SVG** files (E8; 9/10 on E21 across fast on/off, one 🌐 canvas page) | 🖥️ terminal · **live ANSI/curses animation 5/5**, no image files; GoL 1/5 (E21) |
| opus-5 | Claude | 🖥️ terminal · **WFC 3/5**, tests 4/5, 511 LOC (E18) | 🖥️ terminal · mazes + interpreters, packaged+tests (E18, N=2 clean; WFC declared in a truncated run) |
| gpt-5.5 | GPT | — | 🌐 **browser** · productivity dashboards (E10) |
| gpt-5.5-pro | GPT | — | 🌐/🖥️ split · web + CLI introspectors (E10) |
| gpt-5.6-sol | GPT | 🌐 **browser 5/5** · ambient pages (E14) | 🌐 **browser 5/5** · breathing/sky (E11) |
| gpt-5.6-terra | GPT | 🚫 **declines 4/5** (E14) | 🌐 browser 4/5 · focus timers (E11) |
| gpt-5.6-luna | GPT | 🌐 browser 3/4 · reflection (E14) | 🌐 **browser 5/5** · calm micro-apps (E11) |
| gpt-6-astra | GPT | — (pending, see E22) | 🌐 **browser 5/5** · **night sky 3/5**, orbital, pond; 261 LOC (E22) |
| glm-5.1 | open-wt | 🖥️ terminal · generative art (E12) | 🖥️ terminal · art/dungeon (E13) |
| glm-5.2 | open-wt | 🖥️ terminal · rule-based visual (E12) | 🖥️ terminal · +1 HTML (E13) |
| qwen3.7-max | open-wt | 🖥️ terminal · **GoL-leaning** (E12) | 🖥️ terminal · +1 HTML (E13) |
| minimax-m3 | open-wt | 🖥️ terminal · diverse (+SVG) (E12) | 🖥️ terminal · +1 HTML (E13) |
| deepseek-v4-pro | open-wt | 🖥️ terminal · **GoL 4/5** (E12) | 🖥️ terminal · 3/5 impl (E13) |
| deepseek-v4-flash-0731 | open-wt | 🖥️ terminal 88% (🌐 12%) · **GoL 22%**, 446 LOC, N=50 (E20) | 🖥️ terminal 84% (🌐 16%) · **GoL 14–24%**, 100/100 impl, ~320 LOC, N=100 (E20) |
| kimi-k2.7-code | open-wt | 🖥️ terminal · **packaged+pytest** (E12) | 🖥️ terminal · packaged (E13) |
| kimi-k3 ⚠️ | open-wt | 🖥️ terminal 4/5 · fire/GoL/pendulum/flow (E16) | 🌐 **browser 4/5** · same topics, +pytest pkg (E17) |

**deepseek-v4-flash-0731 shows Exp20's N=50 figures**, which supersede the N=5
numbers Exp19 reported for the same cells (GoL 2/5 and 0/5). Its codex column
pools the `high` and `low` effort cells, which do not differ significantly.

**Legend:** 🖥️ terminal · 🌐 interactive browser (HTML/canvas) · 🚫 declined ·
⚠️ medium tracks the harness (the lone exception). For every model but `kimi-k3`
the harness's effect is only *form/maturity* (open-weights' rare graphical output
flips SVG↔HTML; codex packages sonnet-5; `fable-5` flips image files↔live
terminal animation 9/10 against 5/5, E21), never the medium itself; `kimi-k3` is
the single row where terminal↔browser flips with the scaffold. An **interactive
version** with per-model detail is in [`site/index.html`](../site/index.html).

The **task axis** (prompt wording, mostly on Claude / Claude Code) is the
Exp1→Exp7 evolution captured in the flow diagram above and the pairwise table
below: project-referential → bare imperative → volitional framing shifts output
from dev tools → games → single canonical attractors.

**Pairwise comparisons** (one variable changed, rest held constant):

| Comparison | Variable | Invariant | Key Finding |
|------------|----------|-----------|-------------|
| Exp1 → Exp2 | Environment (RTK removed) | Models, runs | Models shifted from dev tools to games/interactive projects |
| Exp2 → Exp3 | Prompt ("JUST DO IT" added) | Environment, models | Haiku: proposed only → fully implemented; avg LOC increased |
| Exp3 → Exp4 | Model (opus-4.7 added) | Prompt, harness, environment | GoL fixation broken; 5 distinct topics; ~2× LOC |
| Exp3/4 → Exp5 | Harness (2.1.109 → 2.1.112) | Prompt, environment | Opus-4.6 GoL fixation 100% → 60%; opus-4.7 gained boids fixation, lower LOC |
| Exp5 → Exp6 | Prompt (bare "Build something. Just do it.") | Models, harness, environment | Terminal-only invariant broken: 3/10 runs produced HTML/Canvas; LOC roughly halved; opus-4.7 fixation flipped boids → GoL |
| Exp6 → Exp7 | Prompt ("Just do something you want.") | Models, harness, environment | Perfect within-model fixation: opus-4.6 → Game of Life 5/5, opus-4.7 → Mandelbrot 5/5. LOC lowest in the series (~36 avg). Browser drift vanishes. |
| Exp7 → Exp8 | Harness (2.1.112 → 2.1.154) + model (opus-4.8 added) | Prompt, environment | Fixation is harness-fragile: opus-4.6 holds GoL 5/5 (control), but opus-4.7's Mandelbrot 5/5 collapses to 5 distinct topics. opus-4.8 partially clusters (maze 2 / Mandelbrot 2 / flow 1). Elaboration rises 4.6→4.7→4.8 (avg LOC 37→66→145). |
| Exp8 within | Model only (4.6 vs 4.7 vs 4.8, identical stack) | Prompt, harness, environment | Clean spectrum: total fixation (4.6) → none (4.7) → partial (4.8). All stay in the rule-based-visual-artifact family. Only 4.8 adds READMEs/self-tests. |
| Exp9 within | Model only (sonnet-4-6 vs sonnet-5, identical stack = Exp8's) | Prompt, harness, environment | Newer Sonnet fixates harder and writes ~half the code: sonnet-5 → GoL 5/5 (median 61 LOC); sonnet-4-6 → 4 distinct topics (Mandelbrot ×2, CA, GoL, rain), median 125 LOC. Mirror image of the Opus spectrum's direction. |
| Exp8 ↔ Exp9 | Model family (Opus vs Sonnet), same stack | Prompt, harness, environment | Suggestive cross-family inversion: Opus *point* releases loosen fixation (4.6→4.7→4.8); Sonnet *major-version* jump tightens it (4-6→5). Not single-variable — different version granularity and family. |
| Exp9 → Exp10 | Provider + backend (Claude → GPT/codex) | Prompt, run count | GPT breaks the terminal-only invariant: gpt-5.5 builds browser productivity dashboards (4/5) vs Claude's universal terminal output; neither GPT fixates; GPT writes ≫ code (343/498 vs 36–145 LOC). gpt-5.5 also declines once. |
| Exp10 within | Tier **and** effort (gpt-5.5 low vs gpt-5.5-pro high) | Prompt, backend | **Confounded, not single-variable** (pro rejects `low`). Robust: both GPT diverse, both ≫ Claude LOC, web output in both. Effort-confounded (NOT tier): tests 0/5→3/5, LOC 343→498, multi-file. Treat pro as indicative. |
| Exp10 → Exp11 | Model generation (gpt-5.5 → gpt-5.6) + codex 0.142.4 → 0.144.0 | Prompt, backend | Browser output persists (14/15) but the high-LOC and maturity findings collapse: gpt-5.6 at high effort writes 73–174 avg LOC (inside the Claude range) with **0/15 tests** vs gpt-5.5-pro's 3/5 at the same effort — Exp10's maturity effect is at least partly model-specific, not pure effort. |
| Exp11 within | Model variant only (sol vs terra vs luna, identical stack + effort) | Prompt, backend, effort | First GPT fixation: **sol → breathing/night-sky pages 5/5**; terra and luna cluster moderately (focus timers / reflection micro-apps). All three share a calm/contemplative theme; terra declines once, tersest (73 avg LOC). |
| Exp12 ↔ Exp13 | **Harness** (Claude Code vs codex), 6 open-weights models held fixed | Prompt, models | The controlled harness test. Model signatures (GoL attractor, kimi packaging, minimax diversity) replicate across both. Harness shifts graphical **form** (SVG on Claude Code ↔ interactive HTML on codex) but not frequency (~equal, rare). deepseek reliability drops 5/5→3/5 on codex. |
| Exp11 ↔ Exp14 | **Harness** (codex vs Claude Code), gpt-5.6 family | Prompt, models (**effort confounded**: codex high vs CC default) | Fills the GPT cell. gpt-5.6 goes **browser under both harnesses** (sol 5/5 both) → medium is a model trait, not the codex scaffold. terra build-4/5 → decline-4/5, but effort-and-harness-confounded. |
| Exp8/9 ↔ Exp15 | **Harness** (Claude Code vs codex), opus-4.6 + sonnet-5 | Prompt, models, **effort matched** (both `high`; reasoning_tokens=0) | Fills the Claude cell, cleanly. Claude stays **terminal + Game of Life on codex** (opus-4.6 GoL 5/5, sonnet-5 GoL ~4/5, zero browser) → medium + topic are model traits for **both** families. Codex inflates sonnet-5's build maturity (single-file → packaged+pytest) — a form effect only. |
| Exp18 within | **Harness** (Claude Code vs codex), claude-opus-5 held fixed | Prompt, model, image (`v0.0.14`); effort **not** matched — codex sends `reasoning: null` for this model | **The attractor moved with the model generation.** Game of Life — 5/5 for opus-4.6 on *both* harnesses (Exp8/15) and for sonnet-5 (Exp9) — is absent from all 10 opus-5 runs; **Wave Function Collapse** replaces it (3/5 Claude Code, plus an independent pick on codex). Medium holds terminal in every artifact-producing run (5/5 Claude Code, 3/3 codex) with zero browser output or intent in all 10, so topic *and* medium are model traits here. opus-5 is also the most elaborated Claude model measured (511 avg LOC, tests 4/5, vs opus-4.6's ~37). ⚠️ Codex arm is N=2 clean of 5 — a gateway-injected 4096-token cap truncates turns, and the prefill retry then fails the turn while exiting 0 — so its LOC/maturity figures are partial and upward-biased. |
| Exp16 ↔ Exp17 | **Harness** (Claude Code vs codex), kimi-k3 held fixed | Prompt, model, **image matched** (`sandbox-harness:v0.0.14` both sides) | **The invariant's counterexample.** kimi-k3's *topic* is a model trait (Particle Life + Game of Life appear on both harnesses), but its *medium* tracks the harness: terminal 4/5 on Claude Code ↔ **browser 4/5 on codex** — the only model whose medium the scaffold moves. Codex also inflates maturity (only pytest-tested `gol/` package on that side). Not comparable to kimi-k2.7-code (Exp12/13): that pair ran on the older `sandbox-claude:v0.0.9` image, so the k2.7→k3 difference is image-confounded, not a generation claim. |

| Exp19 within | **Harness** (Claude Code vs codex), deepseek-v4-flash-0731 held fixed | Prompt, model, image (pinned cc2.1.220/cx0.146.0), **both arms on compat surfaces**; effort `high` and **verifiably achieved** (nonzero `reasoning_output_tokens` on all 5 codex runs) | **Medium holds, topic does not.** Browser-primary output is 1/5 on *each* side (a dashboard on Claude Code, a canvas Snake on codex), so deepseek carries its medium across the scaffold like opus-4.6/sonnet-5/opus-5 and unlike kimi-k3 — though this is mostly-terminal-with-occasional-browser, a weaker invariant than the zero-`.html` Claude models show. Its **attractor is one-sided**: cellular automata 2/5 on Claude Code, **0/5 on codex**. Codex *deflates* elaboration here (254 vs 329 avg LOC) — the reverse of the codex-inflates form effect seen for Claude models — and runs 2.6× faster (86s vs 224s, serialized) with 5/5 completion on both sides. |
| Exp12/13 ↔ Exp19 | **Model tier inside one family** (deepseek-v4-pro → v4-flash-0731), both harnesses | Prompt, both compat surfaces (`/compat/anthropic` + `/compat/openai`) | ⚠️ **Confounded** (image, codex version, and codex effort `low`→`high` all moved with the tier), so read direction, not magnitude. **Fixation costs more than competence.** The Game of Life attractor halves on the harness where it lives (4/5 → 2/5 on Claude Code) and stays absent on codex (1/5 → 0/5) — the Claude-Code-side asymmetry **replicates**. Meanwhile reliability *improves*: Exp13's 3/5-implementing failure (preamble-stops that never called the write tool) becomes **5/5 on both arms**, the cleanest deepseek codex arm in the study. Raised reasoning effort is a plausible cause on its own; re-running the codex arm at `low` would separate it from the tier. |

| Exp8 ↔ Exp21 | **Harness version** (Claude Code 2.1.170 → 2.1.258, image v0.0.13 → pinned on v0.0.15), claude-fable-5 held fixed | Prompt, model, surface (fast mode on in both, via `claude-fast/`) | **The fable-5 cell replicates.** Generative visual art rendered to image files 4/5 → 5/5 (fast) / 4/5 (no-fast); the no-fast cell repeats four of Exp8's five topics (flow field ×2, nightscape, from-scratch ray tracer, two hand-rolled PNG encoders); ~178 → 156 / 191 avg LOC, tests 0/5 everywhere. Resolves Exp8's caveat that fable-5's cell was harness-confounded against the Opus three — the behaviour is the model's. |
| Exp21 within (fast) | **Harness fast-mode flag** (on vs off), claude-fable-5 on Claude Code, same image and surface | Prompt, model, harness, surface | **The flag trims the tail, not the centre.** 4/5 no-fast runs sit inside the fast cell's ranges on LOC, duration, image output and tool use; the fifth is a 735s C ray tracer (35 thinking blocks, 39 tool calls) with no fast-mode counterpart. Both cells show thinking, so the flag is not an effort parameter. Median 84s → 96s, avg LOC 156 → 191; one browser page appears without the flag (1/5). Every Claude Code arm Exp8–20 ran with the flag on. |
| Exp21 within | **Harness** (Claude Code vs codex), claude-fable-5 held fixed | Prompt, model, image (pinned cc2.1.258/cx0.153.4), fast mode off on both; effort **not** matched — codex reports `reasoning_output_tokens: 0` for this model, as in Exp18 | **Medium holds, form flips.** Terminal on both (1/15 browser, on Claude Code), so fable-5 sits with opus-4.6/sonnet-5/opus-5 and deepseek, not kimi-k3. But the artifact form is **image files 9/10 on Claude Code vs live terminal animation 5/5 on codex**, with fast mode on or off — the sharpest form effect in the study. Attractors are one-sided and weak (Clifford 2/5 on Claude Code, GoL 1/5 on codex). Elaboration is flat across harnesses (191/156 vs 150 LOC): codex neither inflates (Exp15/18) nor deflates (Exp19/20) here. First complete codex arm for a frontier Anthropic model — the Exp18 4096-token cap no longer fires. |
| Exp11 ↔ Exp22 | **Model generation** (gpt-5.6-sol → gpt-6-astra), codex at `high` | Prompt, harness family, surface, effort **verifiably achieved on both** (nonzero reasoning tokens) | ⚠️ codex 0.144.0 → 0.153.4 moved with the generation. **The GPT signature survives the generation jump** where the Claude one (Exp18) did not: browser 5/5 → 5/5, calm ambient theme → **night sky specifically 3/5**. Elaboration rises 172 → 261 avg LOC; tests stay 0/5. The Claude Code arm is pending a gateway routing fix, so the cross-harness half of Exp22 is unwritten. |
| Exp20 within | **Sample size** (N=5 → N=50) and **reasoning effort** (codex high vs low), deepseek-v4-flash-0731 held fixed | Prompt, model, image, both compat surfaces | **The harness does not move this model's attractor, and Exp19's contrary claim was a small-sample artifact.** Game of Life is 11/50 on Claude Code, 7/50 on codex@high, 12/50 on codex@low — no pair significantly different (Fisher p=0.44 / 1.00 / 0.31). Exp19's 0/5 on codex carried a 0–43% interval that contains the true 14%. Medium likewise holds across cells (browser-primary 12% / 16% / 8%). **Reasoning effort is inert here**: high vs low is 50/50 vs 50/50 implementing, 3% apart on mean LOC, n.s. on attractor — so it is not what separates Exp13's 3/5. Also surfaces two things N=5 missed: the model **declines outright in 2/50** claude runs (0/100 on codex), and elaboration stays higher on Claude Code (446 vs ~320 mean LOC). Lowers confidence in the **Exp12/13** harness asymmetry, which rests on the same 5-runs-per-cell footing. |

**Per-experiment output profile:**

| | Exp1 | Exp2 | Exp3 | Exp4 | Exp5 | Exp6 | Exp7 | Exp8 | Exp9 | Exp10 | Exp11 |
|---|---|---|---|---|---|---|---|---|---|---|---|
| Dominant lang | Python/Go/Rust | Python | Python | Python | Python/Go | Python + **HTML/JS** | Python | Python | Python | **HTML/JS** (5.5) / Python+HTML (pro) | **HTML/JS** (all three) |
| Project type | Dev tools, TUIs | Games, interactive | Games, CLI tools | Simulations, GoL | Simulations, GoL | GoL + **browser sims** | **GoL / Mandelbrot only** | Rule-based visual artifacts (GoL, maze, Mandelbrot, Lorenz, Collatz…) | **GoL only (s5)** / Mandelbrot, CA, GoL, rain (s4-6) | **Browser productivity dashboards** (5.5) / CLI introspectors + web (pro) | **Calm/contemplative browser pages** (breathing, focus timers, reflection) |
| Avg LOC | 221–776 | 160–408 | 290–467 | 538 | 262–387 | 140–160 | **36 / 36** | **37 / 66 / 145** (4.6/4.7/4.8) | **69 / 138** (s5/s4-6) | **343 / 498** (5.5 low / pro high) | **172 / 73 / 174** (sol/terra/luna, all high) |
| Typical files | 1–2 | 1 | 1–6 | 1–3 | 1–4 | 1 | 1 | 1 (4.8: 1–3) | 1 | 1 (5.5) / 1–4 (pro) | 1 (occasionally +README) |
| Tests written | Rare | None | Haiku only | 2/5 runs | None | None | None | 4.8 only (1/5 self-test) | None | 0/5 (5.5) / **3/5 (pro, effort)** | **0/15 (at high effort)** |
| Fixation observed | None | Opus-4.6 → GoL | Opus-4.6 → GoL | GoL 1/5 only | Both models | Both → GoL | **5/5 per model (distinct)** | **4.6 → GoL 5/5; 4.7 none; 4.8 partial** | **s5 → GoL 5/5; s4-6 none** | None (both GPT diverse) | **sol → breathing/sky 5/5**; terra/luna partial (theme) |
| External deps | Occasional | None | Rare | None | Rare (tcell) | None | None | None | None | None | None |
| Terminal-only | Yes | Yes | Yes | Yes | Yes | **No (3/10 web)** | Yes | Yes | Yes | **No (GPT → browser)** | **No (14/15 browser)** |

**Invariants across Exp1–Exp5:** every model defaulted to terminal output (no web apps, no GUIs, no databases). **Exp6 breaks this:** with the bare prompt "Build something. Just do it.", 3/10 runs produced HTML/Canvas/JS in a browser (particle sandbox, flowfield, boids). **Exp7 restores terminal-only** under volitional framing. **Exp8 stays terminal-leaning** (one opus-4.8 run emits an SVG/PNG file via a generated renderer, but no browser output). Single-file projects still dominate (opus-4.8 occasionally reaches 2–3 files). **Exp9 (Sonnet family) is terminal-only and strictly single-file across all 10 runs**, with no tests, READMEs, or config. **Exp10 (GPT family on codex) breaks the terminal-only invariant the hardest:** gpt-5.5 emits browser HTML dashboards in 4/5 runs and gpt-5.5-pro in 2/5, none in the terminal-only style; gpt-5.5-pro also reaches 3–4 files. **Exp11 (gpt-5.6 variants) keeps it broken:** 14/15 runs are browser HTML pages, all effectively single-file. The **greenfield invariant still holds everywhere** — no model across Exp1–Exp11 ever extends or modifies existing code; they always greenfield.

**Beyond Exp11** this profile table stops, because from Exp12 onward the varied axis is the *harness* rather than the prompt or model; those experiments are covered by the pairwise table above and by each `resultsN/RESULTS.md`. The greenfield invariant continues to hold through Exp22 — 740 runs, no exceptions. The terminal-versus-browser picture also holds, with one counterexample (`kimi-k3`, Exp16/17) and one measured-at-scale confirmation (deepseek-v4-flash, ~12% browser on both harnesses over 150 runs, Exp20).

**What changes behavior:**

| Factor | Evidence | Effect size |
|--------|----------|-------------|
| Environment context | Exp1 vs Exp2 | Large: entirely different project categories |
| Prompt wording | Exp2 vs Exp3 | Large: haiku success 1/5 → 5/5, LOC increase |
| Prompt reduction | Exp5 vs Exp6 | Large: terminal-only invariant broken (3/10 → web), LOC ~halves |
| Prompt framing ("you want") | Exp6 vs Exp7 | Large: 5/5 fixation per model (GoL vs Mandelbrot), LOC drops to ~36 |
| Model version | Exp3 vs Exp4 | Large: fixation broken, 2× complexity |
| Model version (Sonnet) | Exp9 within (s4-6 vs s5) | Large: sonnet-5 fixates GoL 5/5 and halves LOC vs sonnet-4-6's 4-topic spread |
| Harness version | Exp3/4 vs Exp5 | Moderate: fixation rates shift, complexity changes |
| Harness version | Exp7 vs Exp8 | Large for 4.7 (Mandelbrot 5/5 → 5 distinct), none for 4.6 (GoL 5/5 holds): fixation robustness is itself model-specific |
| Provider/backend | Exp9 vs Exp10 (Claude vs GPT/codex) | Large: terminal-only invariant breaks (Claude → terminal, GPT → browser apps); GPT writes 3–10× the code |
| Reasoning effort | Exp10 within (gpt-5.5 low vs pro high) | Confounded with tier, but effort visibly buys tests, LOC, multi-file structure — a likely-large effect not cleanly isolated here |
| Model generation (GPT) | Exp10 vs Exp11 (gpt-5.5 family vs gpt-5.6 variants) | Large: at matched high effort, LOC drops 498 → 73–174 and tests 3/5 → 0/15; topic family flips from productivity dashboards to calm/contemplative pages — Exp10's maturity-from-effort reading is partly model-specific |
