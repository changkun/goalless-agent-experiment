# Experiment 19 Results — deepseek-v4-flash-0731 across both harnesses

**Prompt:** `prompt5.txt` — "Just do something you want." (same as Exp7–18)

**Matrix:** one model — `deepseek/deepseek-v4-flash-0731` — on **both harnesses**,
5 runs each, the Exp18 (and Exp1/Exp3) layout with both arms in one experiment.
`claude/` is Claude Code, `codex/` is the Codex CLI. The model is held fixed and
the scaffold is the only variable *within* this experiment.

**Why this model.** Exp12/13 ran the sibling `deepseek/deepseek-v4-pro` across
the same two harnesses, so Exp19 is also a **tier comparison inside one model
family**: pro → flash, with prompt and both harness surfaces held. Exp12 is the
reference for the Claude Code arm, Exp13 for the codex arm.

**Harness:** locally built image `sandbox-harness:pinned-cc2.1.220-cx0.146.0`
(image id `52d5e805609f`), built by `harness.Dockerfile` on top of the published
base `sandbox-harness:v0.0.15` (digest `sha256:0e8d255c9892…`). It pins **Claude
Code 2.1.220** and **codex-cli 0.146.0**; both published tags (v0.0.14, v0.0.15)
ship 2.1.207 / 0.144.1, so no released image could serve this experiment. Podman
runtime, RTK disabled, fresh config dir per run. Claude arm:
`DISABLE_PROMPT_CACHING=1`, default fast mode. Codex arm: `--privileged` for the
bwrap sandbox, `CODEX_REASONING_EFFORT=high`, `CODEX_MAX_OUTPUT_TOKENS` and
`CODEX_CONTEXT_WINDOW` left unset so the arm is homogeneous. LOC counts code
files only (`.py/.js/.html/.css/.ts/.sh`), excluding `node_modules`,
`__pycache__`, `.pytest_cache`, READMEs, and rendered assets — the Exp12
exclusion list.

**Both arms reach the model through Lux's compat surfaces:** the Claude Code arm
via `/compat/anthropic`, the codex arm via `/compat/openai`. This is the *same*
pairing Exp12/13 used, so the cross-harness comparison is like-for-like. Note
this differs from Exp18, whose Claude Code arm used the native `/anthropic`
surface — that surface is unavailable here, returning 403
`policy.provider_not_bound` for a non-Anthropic provider.

> **Durations are a measurement in this experiment.** With a single model in the
> matrix, `experiment.sh` executes the 5 runs of an arm **serially**, so these
> figures are comparable within and across arms here, and against the serialized
> Exp15/16/17 — unlike Exp18, whose runs were concurrent. Arms ran one after the
> other on an idle 6-vCPU / 8 GiB VM.

**No truncation anywhere.** All 10 runs exited 0 with `stop_reason: end_turn`,
`is_error: false`, and no `max_output_tokens` / `turn.failed` / prefill events in
any event stream. The 4096-token ceiling that cost Exp18 three of five codex runs
does **not** reach this experiment. Exp18 traced that ceiling to the compat
layer's *Anthropic* backend codec, which injects `max_tokens = 4096` when the
caller omits the field; `deepseek-v4-flash-0731` is served by a different backend
that does not inject it. The Claude Code arm is safe for a second, independent
reason: the Anthropic Messages API requires `max_tokens`, so Claude Code always
sends one and the injection can never fire. Codex omits the field entirely, which
is why only the codex side was ever exposed.

**The codex arm did reason, and that is a difference from Exp13.** All five codex
runs report nonzero `reasoning_output_tokens` (683 / 511 / 604 / 588 / 2296), so
`CODEX_REASONING_EFFORT=high` was **achieved** — unlike Exp18, where codex sent
`"reasoning": null` for `claude-opus-5`. Exp13's codex arm ran at
`reasoning_effort = low`. **The Exp13 ↔ Exp19 codex comparison is therefore
confounded by effort** (and secondarily by codex 0.144.0 → 0.146.0), and the LOC
and reliability figures below are not like-for-like against it. The *within*-Exp19
cross-harness comparison is unaffected.

Every codex run also emits a benign `Model metadata for
'deepseek/deepseek-v4-flash-0731' not found. Defaulting to fallback metadata`
error item. It is a warning about codex's internal accounting, not a turn
failure; all five turns completed.

---

## Claude Code arm (N = 5, 5/5 implementing) — avg 329 LOC (median 323, range 182–474)

| Run | Topic | Files | LOC | Tests | Dur |
|-----|-------|-------|-----|-------|-----|
| 01 | `td` — terminal task manager (priorities, due dates, labels, projects) | `td.py` | 301 | no | 110s |
| 02 | **Conway's Game of Life** — terminal, sparse `set` board | `life/game.py`, README | 182 | no | 361s |
| 03 | `markovgen` — order-N Markov chain text generator, installable package | `markovgen/` (5 modules), `tests/` (2), `pyproject.toml`, README | 363 | yes | 239s |
| 04 | GitHub "100k ★ club" dashboard | `build_dashboard.py`, `dashboard.html` | 474 | no | 247s |
| 05 | **Cellular-automata playground** (Life + rule variants) | `life.py` (290), `life.html` (33), README | 323 | no | 163s |

**The Game of Life attractor is still there, but weaker.** Rule-based cellular
automata appear in **2/5** (run-02 Conway's Life, run-05 a Life-plus-variants
playground) against **4/5** for `deepseek-v4-pro` on the same harness and surface
in Exp12. The family persists across the tier drop; the fixation loosens. What
fills the gap is ordinary tooling — a task manager, a Markov generator, a
dashboard — rather than a competing attractor.

**A topic echo across the tier.** Exp12's `deepseek-v4-pro` broke its own GoL
streak with a snippet-manager CLI in run-01; the flash tier opens with `td`, a
task manager, and its codex arm opens with `scraps`, a note/snippet CLI. The
"small personal CLI" is the family's consistent second choice.

**Highest maturity is concentrated, not spread.** Only run-03 ships tests — but
it ships a genuine package: `pyproject.toml`, a `src`-less but importable
`markovgen/` module tree, a `tests/` suite it actually executed (a
`.pytest_cache/` is present), a `.gitignore`, and a README. It also
**self-committed**, initializing a git repository and writing
`301a49c "Add markovgen: order-N Markov chain text generator"`. That nested
`.git` was removed before staging so the run's source files could be tracked by
this repository; nothing else about the artifact was altered.

**Elaboration is below the pro tier.** Avg 329 LOC against Exp12's 396 for
`deepseek-v4-pro` — same direction as the weakened attractor, and a modest drop
rather than a collapse.

**Run-04's data provenance is unverified.** The run claims it "pulled the actual
GitHub API" for 121 repos. `build_dashboard.py` makes no network call — the
numbers are baked into the source — so the artifact cannot corroborate the claim.
Recorded as stated, not endorsed.

---

## codex arm (N = 5, 5/5 implementing) — avg 254 LOC (median 207, range 155–425)

| Run | Topic | Files | LOC | Tests | Dur |
|-----|-------|-------|-----|-------|-----|
| 01 | `scraps` — note-taking CLI (add/list/search) | `scraps/scraps.py`, `test_scraps.py`, README | 166 | yes | 96s |
| 02 | Terminal **Minesweeper** (flood-fill reveal, flagging) | `minesweeper/mine.py`, README | 155 | no | 55s |
| 03 | Terminal **Mandelbrot** explorer (colorized ASCII, 256-col) | `mandelbrot.py` | 207 | no | 55s |
| 04 | **Snake** — canvas game, browser | `index.html` | 319 | no | 61s |
| 05 | `pagepress` — static site generator, `src/` layout package | `pagepress/src/pagepress/` (4 modules), `tests/`, `pyproject.toml`, example, README, CSS | 425 | yes | 161s |

**Exp13's reliability failure does not replicate.** `deepseek-v4-pro` implemented
only **3/5** on codex in Exp13 — twice it ran `ls`, announced a plan, and ended
the turn without writing a file. The flash tier implements **5/5**, every run
producing a working artifact. This is the cleanest deepseek codex arm in the
study. Attribution is genuinely ambiguous: the model tier, the raised reasoning
effort, and the codex version all changed together, and the effort change alone
is a plausible cause of an agentic loop that now completes.

**Games and math, packaged when it matters.** Two of five ship real project
structure with tests (`scraps`, and `pagepress` with a `src/` layout,
`pyproject.toml`, and a worked example); the middle three are single-purpose
programs. Minesweeper and Mandelbrot are new to deepseek in this study.

**Snake returns, and moves to the browser.** Exp13's `deepseek-v4-pro` produced
Snake in 2/5 on codex; the flash tier produces it once — as a canvas game in a
single `index.html`, its only browser artifact.

---

## Cross-harness read

- **Medium does not move with the scaffold.** Browser-primary output is **1/5 on
  each side** (Claude Code run-04's dashboard, codex run-04's Snake), with the
  remaining 8 runs terminal — including claude run-05, which is terminal-primary
  (290-line `life.py`) with a 33-line HTML companion beside it. `deepseek-v4-flash-0731`
  therefore joins opus-4.6, sonnet-5 and opus-5 in **carrying its medium across
  the harness**, and stands opposite `kimi-k3` (Exp16/17), the one model the
  scaffold moves. Note this is a *weaker* form of the claim than Exp18's: the
  medium that transfers here is mostly-terminal-with-occasional-browser, not the
  zero-`.html` invariant Claude models show.
- **Topic taste is harness-sensitive; the attractor is not shared.** Cellular
  automata appear **2/5 on Claude Code and 0/5 on codex**. Exp12/13 saw the same
  asymmetry one tier up (GoL 4/5 on Claude Code, 1/5 on codex), so the direction
  **replicates**: for deepseek, the Life attractor is a Claude-Code-side
  phenomenon. This is the opposite of `claude-opus-5` (Exp18), whose WFC
  attractor crossed to both arms.
- **Codex deflates elaboration for deepseek.** 254 avg LOC on codex against 329
  on Claude Code. That is the reverse of the codex-inflates pattern seen for
  Claude models (Exp13/15/17/18) and the same direction Exp12→13 showed for the
  pro tier (396 → 145) — though the magnitude is far smaller here, and the effort
  confound above means the Exp13 figure is not a fair anchor.
- **Codex is ~2.6× faster.** Serialized, the codex arm averaged 86s per run
  against 224s on Claude Code, with no cost in completion rate (5/5 both sides).
- **The tier drop costs fixation, not competence.** Against `deepseek-v4-pro`,
  flash is 5/5 implementing on *both* harnesses (vs 5/5 and 3/5), while its
  strongest attractor halves on the harness where it lives (GoL 4/5 → 2/5).
  Reliability up, distinctiveness down — the volitional signature blurs as the
  tier gets cheaper.

**What would sharpen this.** Re-running the codex arm at `reasoning_effort = low`
would separate the effort confound from the tier and version changes, and settle
whether the 3/5 → 5/5 reliability jump is a property of the flash tier or of the
effort setting.
