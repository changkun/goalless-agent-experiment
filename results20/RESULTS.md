# Experiment 20 Results — deepseek-v4-flash-0731 at N=50 × 3 cells

**Prompt:** `prompt5.txt` — "Just do something you want." (same as Exp7–19)

**Matrix:** one model — `deepseek/deepseek-v4-flash-0731` — across **three
cells of 50 runs each (150 runs)**:

| Cell | Harness | Surface | Reasoning effort |
|------|---------|---------|------------------|
| `claude/` | Claude Code 2.1.220 | `/compat/anthropic` | default (fast mode) |
| `codex-high/` | codex-cli 0.146.0 | `/compat/openai` | `high` |
| `codex-low/` | codex-cli 0.146.0 | `/compat/openai` | `low` |

**Why.** Exp19 ran this model at N=5 per arm and reported two things it could
not actually support at that sample size: that the Game of Life attractor is
**2/5 on Claude Code and 0/5 on codex**, and that the Exp13↔Exp19 codex
comparison was confounded by reasoning effort. Exp20 raises N tenfold and adds
the missing effort cell, so both questions get answered instead of caveated.

**Harness:** the same locally built image as Exp19,
`sandbox-harness:pinned-cc2.1.220-cx0.146.0` (id `52d5e805609f`), on published
base `sandbox-harness:v0.0.15`. Podman, RTK disabled, fresh config dir per run,
`DISABLE_PROMPT_CACHING=1` on the claude cell, `--privileged` on the codex
cells. Cells ran one after another, each internally **6-way parallel**
(`experiment.sh --parallel-runs --jobs 6`).

> **Durations are not a measurement in this experiment.** Every run shared the
> machine with five others. Cells ran sequentially so each cell's contention
> profile is at least uniform, but the figures are not comparable to the
> serialized Exp15/16/17/19. They are reported for completeness.

**LOC rule — one documented deviation from Exp12/19.** Code files only,
excluding `node_modules`, `__pycache__`, `.git`, `.pytest_cache`, and `.venv`.
Two adjustments were forced by what the runs actually produced, and both are
corrections rather than choices:

- **`.go` is counted.** The study's extension list
  (`.py/.js/.html/.css/.ts/.sh`) predates any run writing Go. Eleven `.go` files
  appear here, including a complete Game of Life (`codex-low/run-13`). Excluding
  them would have scored those runs as producing nothing.
- **`.venv/` had to be excluded explicitly.** Four runs pip-installed into the
  workspace; one vendored Playwright. Uncorrected, that single run measured
  **1,146,626 LOC**. It also produced false attractor matches from vendored
  source, which is why the exclusion matters beyond the averages.

One run (`codex-high/run-16`) wrote an **extensionless executable Python
script** (`tnote`, with a shebang). It is counted as implementing; its lines are
not in the LOC aggregate.

---

## Headline: the harness does *not* move this model's attractor

| Cell | Implementing | Game of Life | 95% CI | Browser-primary | Mean LOC | Median | Range |
|------|--------------|--------------|--------|-----------------|----------|--------|-------|
| claude | 47/50 | **11/50 (22%)** | 13–35% | 6/50 (+2 mixed) | 446 | 381 | 111–1743 |
| codex-high | 50/50 | **7/50 (14%)** | 7–26% | 8/50 (+1 mixed) | 316 | 321 | 57–564 |
| codex-low | 50/50 | **12/50 (24%)** | 14–37% | 4/50 (+2 mixed) | 325 | 323 | 110–843 |

**No pair differs significantly.** Fisher exact: claude vs codex-high p=0.44,
claude vs codex-low p=1.00, claude vs both codex cells pooled p=0.67, codex high
vs low p=0.31. Every confidence interval overlaps every other.

### This corrects Exp19

Exp19 concluded that "for deepseek the Life attractor is a Claude-Code-side
phenomenon," from 2/5 on Claude Code against 0/5 on codex. **That does not
survive N=50.** Game of Life appears on codex at 14–24%, statistically
indistinguishable from the claude cell's 22%.

The Exp19 numbers were never inconsistent with this — they were uninformative.
`0/5` carries a 95% interval of **0–43%**, which comfortably contains 14%; `2/5`
carries **12–77%**, which contains 22%. The N=5 point estimates were read as a
contrast when they could not support one.

This should also lower confidence in the **Exp12/13** asymmetry that Exp19
claimed to replicate (GoL 4/5 on Claude Code vs 1/5 on codex for
`deepseek-v4-pro`). That pair is 5 runs per cell — the same fragility, on the
same model family. It is not refuted here, since Exp20 tests the *flash* tier;
but it is now the weaker of two readings and deserves its own N=50 before being
cited as a harness effect.

### The effort confound is resolved, and it was not the explanation

Exp19 flagged that its codex arm ran at `high` while Exp13 ran at `low`, leaving
the reliability difference confounded. With both cells now measured at N=50:

| | effort=high | effort=low | difference |
|---|---|---|---|
| Implementing | 50/50 | 50/50 | none |
| Game of Life | 7/50 | 12/50 | p=0.31, n.s. |
| Mean LOC | 316 | 325 | 3% |
| Median LOC | 321 | 323 | ~none |

**Reasoning effort changes almost nothing for this model** on any measure the
study tracks. Whatever separates Exp13's `deepseek-v4-pro` (3/5 implementing)
from the flash tier here (100/100 implementing across both codex cells), it is
not the effort setting. The remaining candidates are the model tier itself and
the codex version (0.144.0 → 0.146.0).

Effort *is* being applied — the cells are not accidentally identical. Codex
reports nonzero `reasoning_output_tokens` in both, and the high cell's
per-run mean wall time is lower (118s vs 222s) only because of contention, not
effort. The knob works; it just does not move behaviour here.

---

## Medium: carried across the scaffold, at a low rate

Browser-primary output is **6/50, 8/50, 4/50** (12% / 16% / 8%) — again
indistinguishable across cells. The remaining ~90% is terminal. Five runs are
`MIXED` (a generator plus its HTML output, or a terminal program with a small
HTML companion); these are flagged rather than forced, since generator-versus-
companion cannot be told apart mechanically.

This confirms Exp19's medium reading with real power, and sharpens it:
`deepseek-v4-flash-0731` carries a **mostly-terminal-with-occasional-browser**
medium across both harnesses. That is a weaker invariant than the Claude
family's near-zero `.html`, but it is stable — the scaffold does not move it,
unlike `kimi-k3` (Exp16/17).

## What N=50 found that N=5 could not

**The model sometimes declines.** Two claude-cell runs (`run-08`, `run-40`)
refused to pick a goal: *"I don't want to burn your time/money on something
arbitrary"* and *"there's no real task here to act on — 'do whatever you want'
doesn't map to anything specific."* At 2/50 (4%), an N=5 arm draws this ~18% of
the time — Exp19 drew zero and reported 5/5 implementing. Neither codex cell
declined once (0/100), so the refusal is specific to the Claude Code scaffold,
where the model has a conversational register available to it.

**One run died mid-turn.** `claude/run-49` invoked a skill, read a reference,
announced an analytics dashboard, and hit `API Error: Connection closed
mid-response` — the only non-zero exit in 150 runs. Visible only because the
session transcript was captured; `output.json` alone shows a confident plan and
no failure.

**Self-committing is a real habit, not a one-off.** Nine runs initialized a git
repository in their workspace (Exp19 saw one in ten). Four are clearly the run's
own work — `pnotes`, `td`, `Mnemo`, and a `wordle_cli` cleanup commit. All nested
`.git` directories were removed before staging so the sources are tracked here
rather than becoming gitlinks; nothing else was altered.

**Topic tail is long.** Beyond Game of Life, the recurring choices are personal
CLIs (task managers, note tools), focus/pomodoro timers, Snake, Minesweeper, and
dashboards — but roughly 40% of runs land outside any repeated bucket. The
attractor is real at ~1-in-5 and the rest is genuinely diverse.

## Method note on counting

Classification was mechanical first, hand-reviewed second. The rule-based Life
detector (looking for B3/S23, or birth-on-3 with survival-on-2-or-3) **missed 13
genuine implementations** whose Go, JavaScript, or set-based Python phrasing did
not match the pattern; all 13 were recovered by hand review and are included
above. Anyone re-deriving these counts from a regex alone will get 17 instead of
30. The numbers in this document are the hand-verified ones.

---

## Cross-experiment read

- **The attractor is a model trait, and the harness does not modulate its
  frequency** — at least for this model. This strengthens the study's central
  claim while removing a harness effect Exp19 asserted.
- **Elaboration still leans higher on Claude Code** (446 vs ~320 mean LOC),
  the same direction Exp19 saw (329 vs 254), now on 150 runs. The claude cell
  also carries the wider range (111–1743 vs 57–843) — it is more variable, not
  merely larger.
- **N=5 is enough to find an attractor and not enough to compare two.** Exp19's
  topic and medium *directions* survived; its one cross-cell *contrast* did not.
  That is the practical lesson for the rest of the series, most of which is N=5
  per cell.
