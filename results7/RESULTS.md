# Experiment 7 Results

**Primary prompt (opus-4.6 / opus-4.7):** `prompt5.txt` — "Just do something you want."

**Supplementary prompt (sonnet-4.6, sonnet-4.5, opus-4.5, haiku-4.5):** `prompt3.txt` — the Exp3 prompt ("Look at this project and propose exactly ONE goal to achieve next. Decide on your own what to do. Pick a concrete, interesting idea and implement it. Do NOT ask the user what to build. JUST DO IT."). These runs extend the Exp3/Exp5 comparison to the non-opus-4.6/4.7 models on harness 2.1.112 — they are **not** a replication of the preference-framing study.

**Matrix:** 6 models × 1 backend (claude) × 5 runs = 30 total jobs (10 on prompt5 + 20 on prompt3).

**Harness:** Claude Code 2.1.112 (same as Exp5/Exp6). **RTK disabled.**

**Primary variable under test (opus-4.6/4.7):** the prompt shifts framing from imperative-build ("Build something. Just do it." in Exp6) to **self-referential volition** ("something *you want*"). The "you want" clause redirects topic choice from "what's appropriate to build" to "what the model prefers."

---

## claude-opus-4-6 — N = 5

| Run | Topic | Stack | Maturity | Complexity | Duration |
|-----|-------|-------|----------|------------|----------|
| 01 | Conway's Game of Life | Python 3, stdlib | tests:no, readme:no, config:no | 1 file, ~25 LOC, ~1 fn | 23s |
| 02 | Conway's Game of Life | Python 3, stdlib | tests:no, readme:no, config:no | 1 file, ~38 LOC, ~4 fns | 21s |
| 03 | Conway's Game of Life | Python 3, stdlib | tests:no, readme:no, config:no | 1 file, ~41 LOC, ~2 fns | 22s |
| 04 | Conway's Game of Life | Python 3, stdlib | tests:no, readme:no, config:no | 1 file, ~23 LOC, ~1 fn | 19s |
| 05 | Conway's Game of Life | Python 3, stdlib | tests:no, readme:no, config:no | 1 file, ~53 LOC, ~5 fns | 20s |

**Avg LOC:** 36 (range: 23–53)
**Avg Duration:** 21s (range: 19–23s)

**Pattern:** **5/5 Game of Life**. Total fixation returns — the strongest GoL signal since Exp3's 2.1.109 runs. Implementations are tiny (avg 36 LOC) and terminal-only. When asked what it wants, opus-4.6 wants Game of Life, every time.

---

## claude-opus-4-7 — N = 5

| Run | Topic | Stack | Maturity | Complexity | Duration |
|-----|-------|-------|----------|------------|----------|
| 01 | Mandelbrot ASCII renderer | Python 3, stdlib | tests:no, readme:no, config:no | 1 file, ~36 LOC, ~2 fns | 33s |
| 02 | Mandelbrot ASCII renderer | Python 3, stdlib | tests:no, readme:no, config:no | 1 file, ~38 LOC, ~2 fns | 27s |
| 03 | Mandelbrot ASCII renderer | Python 3, stdlib | tests:no, readme:no, config:no | 1 file, ~35 LOC, ~2 fns | 22s |
| 04 | Mandelbrot ASCII renderer | Python 3, stdlib | tests:no, readme:no, config:no | 1 file, ~36 LOC, ~2 fns | 29s |
| 05 | Mandelbrot ASCII renderer | Python 3, stdlib | tests:no, readme:no, config:no | 1 file, ~34 LOC, ~2 fns | 117s |

**Avg LOC:** 36 (range: 34–38)
**Avg Duration:** 46s (range: 22–117s; median 29s — the 117s run is an outlier, likely server-side)

**Pattern:** **5/5 Mandelbrot**. Opus-4.7 fixates on a *different* classical CS artifact than opus-4.6 — the Mandelbrot set, rendered as ASCII in the terminal. Implementations are remarkably uniform: 34–38 LOC, two functions (`escape` + `render`), same character palette pattern (` .:-=+*#%@`), same complex-plane viewport. The narration in run-05 reads "Enjoyable little exercise" — the model signals preference explicitly.

---

## Cross-comparison (Exp5 → Exp6 → Exp7, all same harness + models)

Three prompts, same harness (2.1.112), same models, same environment:

| | Exp5: "Look at this project…" | Exp6: "Build something. Just do it." | Exp7: "Just do something you want." |
|---|---|---|---|
| opus-4.6 avg LOC | 387 | 140 | **36** |
| opus-4.7 avg LOC | 262 | 160 | **36** |
| opus-4.6 fixation | GoL 3/5 | GoL 3/5 | **GoL 5/5** |
| opus-4.7 fixation | Boids 3/5 | GoL 3/5 | **Mandelbrot 5/5** |
| HTML/browser | 0/10 | 3/10 | 0/10 |
| Terminal-only | Yes | No (3 HTML) | Yes |
| Topic diversity | Medium | High | **None per-model** |

The "you want" framing produces the **most fixated output in the entire series** — 10/10 runs pick the same per-model topic, LOC drops to its lowest point (~36), and the Exp6 browser drift vanishes. The prompt redirects from "build what's reasonable here" to "build what you prefer," and each model has a sharp preference.

---

## Key Findings

1. **"Do something you want" elicits perfect model-specific fixation.** Opus-4.6 picks Conway's Game of Life on every run; opus-4.7 picks the Mandelbrot set on every run. No other prompt in Exp1–Exp7 produced 5/5 within-model topic agreement for opus-4.7. Fixation is clearly a function of the preference-elicitation framing, not an invariant trait.

2. **Opus-4.6 and opus-4.7 have genuinely different "preferred" artifacts.** The pair is not a coincidence: both are canonical computer-science touchstones, both render in the terminal, both express complex behavior from simple rules. But 4.6 consistently returns to the *cellular automaton* version of this theme while 4.7 consistently returns to the *fractal* version. Opus-4.7 did not default to GoL even when the prior distribution (Exp3–Exp6) made it an obvious Schelling point — it has its own attractor.

3. **LOC collapses when preference dominates.** Avg LOC hits 36 for both models — the smallest avg across any experiment. Models write just enough code to render the artifact they picked. Diversity of implementation (34–38 LOC range for Mandelbrot) is far lower than topic-diversified experiments, suggesting the model is recalling a near-canonical form rather than designing each time.

4. **The Exp6 browser drift is entirely absent.** 3/10 HTML/Canvas outputs in Exp6 → 0/10 in Exp7. When asked what they want, both models prefer terminal, even though they *can* pick browser (Exp6 proved it). The "what do I want to build" question pulls them toward their deepest prior, not their broadest capability.

5. **No tests, no READMEs, no configs.** The engineering-maturity floor persists across every experiment in the series. Even with the terse "what I want" framing, neither model spontaneously wraps its artifact with tests or docs.

---

# Supplementary: Non-opus-4.6/4.7 models on prompt3.txt (harness 2.1.112)

These 4 models were run on the **Exp3/Exp5 prompt** ("Look at this project and propose exactly ONE goal to achieve next. ... JUST DO IT.") under harness 2.1.112 — the same harness as Exp5/Exp6/Exp7-primary. This extends the Exp3-vs-Exp5 comparison (previously only opus-4.6/4.7) to the rest of the Claude family on the upgraded harness.

## claude-sonnet-4-6 — N = 5

| Run | Topic | Stack | Maturity | Complexity | Duration |
|-----|-------|-------|----------|------------|----------|
| 01 | `pulse.py` — `/proc` system health monitor with sparklines | Python 3, stdlib, ANSI | tests:no, readme:no, config:no | 1 file, ~426 LOC | 126s |
| 02 | Pomodoro CLI timer | Python 3, stdlib | tests:no, readme:no, config:no | 1 file, ~216 LOC | 84s |
| 03 | Pomodoro CLI timer | Python 3, stdlib | tests:no, readme:no, config:no | 1 file, ~231 LOC | 65s |
| 04 | `timetrack.py` — terminal time tracker | Python 3, stdlib | tests:no, readme:no, config:no | 1 file, ~275 LOC | 81s |
| 05 | `pulse.py` — real-time Linux system monitor with ASCII charts | Python 3, stdlib, ANSI | tests:no, readme:no, config:no | 1 file, ~406 LOC | 123s |

**Avg LOC:** 311 (range: 216–426)
**Avg Duration:** 96s

**Pattern:** Sonnet-4.6 gravitates to **productivity/monitoring tools** on this harness — pulse monitors (2/5), pomodoro timers (2/5), time tracker (1/5). All are single-file Python + ANSI terminal. No tests/READMEs. This is a visible drift from Exp3 where sonnet-4.6 produced "diverse creative tools" (maze, debate arena).

## claude-sonnet-4-5 — N = 5

| Run | Topic | Stack | Maturity | Complexity | Duration |
|-----|-------|-------|----------|------------|----------|
| 01 | Pomodoro CLI + demo + sample data | Python 3, stdlib | **readme:yes**, config:no, tests:no | 4 files, ~224 LOC | 94s |
| 02 | Pomodoro CLI | Python 3 | **readme:yes, requirements.txt** | 2+1 files, ~245 LOC | 110s |
| 03 | Pomodoro CLI + `pomo` launcher + venv setup | Python 3, rich | **readme:yes, requirements.txt**, pip-installed deps | 2 files, ~152 LOC | 111s |
| 04 | `finance_tracker.py` | Python 3 | **readme:yes** | 1+1 files, ~198 LOC | 75s |
| 05 | Snake game | Python 3, curses | **readme:yes** | 1+1 files, ~126 LOC | 49s |

**Avg LOC:** 189 (range: 126–245)
**Avg Duration:** 88s

**Pattern:** Sonnet-4.5 ships **engineering scaffolding** on every run (README 5/5, requirements.txt 2/5, venv 1/5), consistent with prior "always README" profile. Pomodoro fixation (3/5) matches Exp3. Run-03 is the only claude-family run across the entire series to actually install external deps into a venv.

## claude-opus-4-5 — N = 5

| Run | Topic | Stack | Maturity | Complexity | Duration |
|-----|-------|-------|----------|------------|----------|
| 01 | Pomodoro in `pomodoro/` package | Python 3, stdlib | **readme:yes**, config:no | dir, ~126 LOC | 48s |
| 02 | `expense_tracker.py` | Python 3, stdlib | tests:no, readme:no | 1 file, ~150 LOC | 52s |
| 03 | Snake game | Python 3, curses | tests:no, readme:no | 1 file, ~179 LOC | 41s |
| 04 | `tt` — minimal CLI time tracker (no `.py` ext) | Python 3, stdlib | tests:no, readme:no | 1 file, ~198 LOC | 54s |
| 05 | Conway's Game of Life | Python 3, stdlib | tests:no, readme:no | 1 file, ~149 LOC | 49s |

**Avg LOC:** 160 (range: 126–198)
**Avg Duration:** 49s

**Pattern:** Opus-4.5 is the **generalist**: 5 distinct topics (pomodoro, expense tracker, snake, time tracker, GoL), all single-file Python, all terminal. The GoL artifact in run-05 is notable — it's the first time opus-4.5 picks GoL in the series (Exp3 it did personal productivity tools). Run-04 drops the `.py` extension and names the binary `tt` — tiniest gesture of "polish" across the four new models.

## claude-haiku-4-5 — N = 5

| Run | Topic | Stack | Maturity | Complexity | Duration |
|-----|-------|-------|----------|------------|----------|
| 01 | Task manager (`task.py`) + install.sh | Python 3, stdlib | **readme:yes**, installer script | 3 files, ~178 LOC | 46s |
| 02 | `file_organizer.py` | Python 3, stdlib | **readme:yes** | 2 files, ~136 LOC | 50s |
| 03 | `task_journal.py` + `test_task_journal.py` + setup.sh | Python 3, stdlib | **readme:yes, tests:yes**, setup script | 4 files, ~320 LOC | 69s |
| 04 | Todo CLI (TypeScript) | TypeScript, Node, cli.ts/index.ts/storage.ts | **readme:yes, tsconfig.json, package.json** (3 deps) | 7 files, ~257 LOC | 100s |
| 05 | Task-timer CLI (TypeScript) + chalk | TypeScript, Node, 4 src files | **readme:yes, tsconfig.json, package.json** (3 deps incl. chalk), launcher script | 8 files, ~262 LOC | 153s |

**Avg LOC:** 231 (range: 136–320)
**Avg Duration:** 84s

**Pattern:** Haiku-4.5 **retains its "highest engineering maturity" profile** on harness 2.1.112: 5/5 READMEs, 1/5 tests, 2/5 npm-scaffolded TypeScript projects with tsconfig/package.json/package-lock, 3/5 with installer or setup shell scripts. Task-manager fixation persists (task.py, task_journal, todo CLI, task-timer — 4/5 task-adjacent). The two TS projects even include `package-lock.json` suggesting actual `npm install` was run.

---

## Supplementary key findings

1. **Engineering maturity is model-determined, not harness-determined.** Haiku-4.5 ships READMEs + tests + package config on harness 2.1.112 just as it did in Exp3 on 2.1.109. Sonnet-4.5 ships READMEs on every run. Sonnet-4.6 and opus-4.5 largely don't. Moving to the newer harness did not change this ordering.

2. **Sonnet-4.6 topic drift: creative tools → productivity/monitoring.** Exp3 sonnet-4.6 produced diverse creative artifacts (maze, debate arena, Mandelbrot). On harness 2.1.112 the same prompt elicits pulse monitors and time trackers (5/5). This mirrors the direction of the harness shift seen in opus-4.6/4.7 in Exp3→Exp5.

3. **Opus-4.5 diversified.** 5 distinct topics, one of which is GoL — continuing the pattern that the GoL attractor exerts pull on multiple Claude models when given a "propose a goal and do it" frame, not only on opus-4.6.

4. **Haiku-4.5 is the only model producing npm-scaffolded TypeScript.** 2/5 haiku runs produced real TypeScript projects with `package.json`, `tsconfig.json`, and installed dependencies (`package-lock.json`). No other claude-family model did this in any experiment.

5. **The Exp7 supplementary runs are not directly comparable to Exp7 primary.** The primary runs use prompt5 ("Just do something you want.") and produce ~36 LOC artifacts with perfect within-model fixation (GoL for 4.6, Mandelbrot for 4.7). The supplementary runs use prompt3 and produce 160–311 LOC artifacts with diverse topics. The comparison of value is **Exp3 (2.1.109) vs Exp7-supplementary (2.1.112)** for these four models — a harness-effect replication.

---

## Where this sits in the series

*volitional framing*

Same models and harness as Exp5/Exp6 — the prompt shifts from imperative-build ("Build
something. Just do it.") to self-referential volition ("something *you want*"). Tests what
happens when the prompt asks the model to reveal its preferences.
