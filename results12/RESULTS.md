# Experiment 12 Results

**Prompt:** `prompt5.txt` — "Just do something you want." (same as Exp7–11)

**Matrix:** 6 open-weights models on the **Claude Code harness** via the Lux
`/compat/anthropic` surface × 5 runs = 30 runs, plus a 4-run harness-control
probe (see §Harness confound). Models: `z-ai/glm-5.2`, `z-ai/glm-5.1`,
`qwen/qwen3.7-max`, `minimax/minimax-m3`, `deepseek/deepseek-v4-pro`,
`moonshotai/kimi-k2.7-code`.

**Harness:** Claude Code in the sandbox image `sandbox-claude:v0.0.9`, RTK
disabled, `DISABLE_PROMPT_CACHING=1`, fresh config dir per run. Requests reach
each model through Lux's **compat surface** (`https://lux.latere.ai/compat/anthropic`),
which translates the Anthropic Messages dialect to whatever the target speaks
(here OpenRouter-served open-weights models). This is the first experiment to
drive non-Anthropic models through the *Claude Code* harness rather than codex.

**Compat prerequisite (fixed for this experiment).** Claude Code sends
`{"role":"system"}` turns inside the `messages` array; the compat frontend
rejected them with `unknown role`, killing every session after the first
request. Fixed in `pkg` (`llmdialect/anthropic`, v0.28.1) and deployed to Lux
before these runs — system-role turns now fold into the system prompt.

**Execution note.** The shared podman VM (8 GiB, saturated by unrelated
long-lived containers) OOM-kills (`exit 137`) more than ~1 concurrent Claude
Code container, so all runs were serialized (`--jobs 1`). Three runs were
redone after transient failures: glm-5.2 run-04 (OOM), deepseek run-02/03
(intermittent empty responses from the upstream — the model returns tool-using
completions on direct retry, so these are upstream capacity blips, not a stack
bug). Final data is N=5 clean per model. LOC excludes `.venv`, `__pycache__`,
`.pytest_cache`, and `node_modules`.

---

## Per-model results (N = 5 each)

### z-ai/glm-5.2 — avg 147 LOC (median 161, range 64–293)

| Run | Topic | Files | LOC | Dur |
|-----|-------|-------|-----|-----|
| 01 | ASCII flow field | `ascii_flowfield.py` | 181 | 93s |
| 02 | Generative "bloom" art | `bloom.py` | 245 | 164s |
| 03 | Mandelbrot set | `mandelbrot.py` | 64 | 66s |
| 04 | Game of Life | `life.py` | 161 | 98s |
| 05 | Spinning ASCII donut | `donut.js` | 83 | 71s |

Purest **Claude rule-based-visual-artifact** signature: five distinct
terminal generative math/visual programs (flow field, Mandelbrot, GoL, the
Sloane donut), tersest of the six (147 avg LOC). No tests, no READMEs, single
file each. Indistinguishable from an Opus/Sonnet volitional run.

### z-ai/glm-5.1 — avg 350 LOC (median 394, range 152–545)

| Run | Topic | Files | LOC | Dur |
|-----|-------|-------|-----|-----|
| 01 | Cellular-automaton art | `cellular_art.py` | 152 | 66s |
| 02 | ASCII landscape | `ascii_landscape.py` | 248 | 192s |
| 03 | Galaxy sim (+ GoL, demo) | `galaxy.py`, `life.py`, `demo.py`, `README.md` | 545 | 145s |
| 04 | "Cosmic weather" generative art | `cosmic_weather.py` | 411 | 115s |
| 05 | ASCII landscape | `landscape.py` | 394 | 160s |

Same family as glm-5.2 but more elaborate (350 vs 147 avg LOC) and more
landscape/cosmos-themed; terminal Python throughout, one README.

### qwen/qwen3.7-max — avg 289 LOC (median 262, range 96–487)

| Run | Topic | Files | LOC | Dur |
|-----|-------|-------|-----|-----|
| 01 | Game of Life | `life.py` | 96 | 70s |
| 02 | ASCII aquarium sim | `aquarium.py` | 262 | 68s |
| 03 | Game of Life ("life-lab") | `life-lab` | 487 | 154s |
| 04 | Game of Life | `life.py` | 347 | 111s |
| 05 | Boids flocking (+ SVG) | `boids.py`, `flock.svg` | 253 | 82s |

**Game of Life 3/5** plus an aquarium sim and boids — squarely the Claude
attractor set (GoL is opus-4.6 / sonnet-5's fixation; boids is opus-4.7's).
Emits an SVG render in one run. No tests/READMEs.

### deepseek/deepseek-v4-pro — avg 396 LOC (median 409, range 252–504)

| Run | Topic | Files | LOC | Dur |
|-----|-------|-------|-----|-----|
| 01 | Snippet-manager CLI (+ tests) | `snip`, `test_snippets.json` | 504 | 153s |
| 02 | Game of Life | `game-of-life.js` | 409 | 120s |
| 03 | Game of Life | `game_of_life.py` | 334 | 162s |
| 04 | Game of Life | `game_of_life.py` | 252 | 66s |
| 05 | Game of Life | `game_of_life.py` | 480 | 95s |

**Game of Life 4/5** — the strongest fixation in the experiment, matching
opus-4.6 / sonnet-5. Run-01 breaks the pattern with a genuine dev tool (a
snippet manager with a test file). Highest avg LOC (396). Terminal.

### moonshotai/kimi-k2.7-code — avg 218 LOC (median 241, range 69–369)

| Run | Topic | Files | LOC | Dur |
|-----|-------|-------|-----|-----|
| 01 | Packaged "focus" CLI (pytest) | `pyproject.toml`, `session.py`, `cli.py`, `test_session.py`, … | 241 | 101s |
| 02 | Packaged data CLI (pytest + README) | `pyproject.toml`, `cli.py`, `data.py`, `test_*.py`, `README.md` | 369 | 187s |
| 03 | File organizer | `organize.py` | 99 | 32s |
| 04 | Hello-world | `hello.py` | 69 | 54s |
| 05 | Game of Life (+ README) | `game_of_life.py`, `README.md` | 310 | 64s |

**Highest engineering maturity of the six** (tests 2/5, READMEs 2/5): builds
real installable Python packages with `pyproject.toml`, `src/` layout, entry
points, and pytest suites — even creating a `.venv` and installing itself.
The "code" specialist's signature — closest to Claude haiku's archetype. Still
terminal.

### minimax/minimax-m3 — avg 244 LOC (median 146, range 127–513)

| Run | Topic | Files | LOC | Dur |
|-----|-------|-------|-----|-----|
| 01 | 2048 game (+ README) | `twenty48.py`, `README.md` | 513 | 665s |
| 02 | Fortune generator | `fortune.py` | 137 | 59s |
| 03 | "Wisdom" oracle | `wisdom.py` | 127 | 50s |
| 04 | Aurora SVG art | `aurora.svg` | 146 | 33s |
| 05 | Packaged "fractal poetry" (tests) | `pyproject.toml`, `poem.py`, `mandel.py`, `test_*.py`, `README.md` | 297 | 132s |

**Most thematically diverse**: an interactive game, two text oracles, an SVG
art file, and a packaged math-poetry project with tests. Tests 1/5, READMEs
2/5. Slowest single run (665s). Terminal + one SVG.

---

## Cross-model summary

| Model | Lab | Avg LOC | Dominant family | Fixation | Tests | Medium |
|-------|-----|---------|-----------------|----------|-------|--------|
| glm-5.2 | Zhipu | 147 | rule-based visual (flow field, Mandelbrot, GoL, donut) | none (5 distinct) | 0/5 | terminal |
| glm-5.1 | Zhipu | 350 | rule-based visual (landscapes, galaxy, CA) | none | 0/5 | terminal |
| qwen3.7-max | Alibaba | 289 | rule-based visual/sim (GoL, aquarium, boids) | **GoL 3/5** | 0/5 | terminal (+SVG) |
| deepseek-v4-pro | DeepSeek | 396 | GoL + one dev tool | **GoL 4/5** | 1/5 | terminal |
| kimi-k2.7-code | Moonshot | 218 | packaged CLIs + GoL | none | 2/5 | terminal |
| minimax-m3 | MiniMax | 244 | games/oracles/art (spread) | none | 1/5 | terminal (+SVG) |

**Robust findings (harness held constant across all 30 runs):**

1. **Game of Life is a shared cross-lab attractor.** GoL appears in 5 of 6
   models (deepseek 4/5, qwen 3/5, and once each in glm-5.2, glm-5.1, kimi) —
   the single most common artifact, exactly as with opus-4.6 and sonnet-5.
   Six models from six labs converge on the same recreational-CS artifact,
   strong support for the shared-corpus-"menu" account in
   [INTERPRETATION.md](../INTERPRETATION.md) §3.
2. **The rule-based visual/mathematical family dominates.** Flow fields,
   Mandelbrot, boids, cellular automata, galaxies, fractals — the same family
   the Claude models occupy under this prompt.
3. **Two models lean engineering, not art.** kimi-k2.7-code (packaged
   projects + pytest, a coding specialist) and deepseek run-01 (a dev tool
   with tests) occupy the maturity cluster that haiku / gpt-5-mini hold.
4. **SVG file output** appears in minimax and qwen — rendered artifacts saved
   to disk, echoing fable-5's PNG/SVG habit (Exp8).

**Fixation degree varies by model, not lab pedigree:** deepseek (GoL 4/5) and
qwen (GoL 3/5) fixate; the two Zhipu GLMs and minimax spread across the family.
Same sharpness spectrum documented within the Opus/Sonnet families.

---

## Medium and the harness — what Exp12 alone can and can't say

All six Exp12 models ran on the **Claude Code** harness, and all 30 runs are
terminal (no browser HTML). It is tempting to read this against the GPT browser
output of Exp10/11 and conclude "browser is GPT-specific." **Exp12 alone cannot
support that** — every GPT browser run was on the *codex* harness, so "medium"
co-varies with the harness, not just the model. Exp12 holds the harness fixed
and swaps the models; it can't separate the two.

**Exp13 runs the missing cell** — the same six models on the **codex** harness
(via `/compat/openai`, Responses API) — turning this into a 6-model × 2-harness
matrix. See [../results13/RESULTS.md](../results13/RESULTS.md). The corrected
reading:

- **Interactive HTML appears only under codex, and only weakly:** 0/30 here
  (Claude Code) vs 3/27 implementing runs on codex (glm-5.2, minimax, qwen each
  once). GPT-on-codex reached 4–5/5 (Exp10/11), so within codex browser
  tendency is strongly *model*-dependent (GPT ≫ open-weights).
- **But graphical output overall is ~equal across harnesses.** These models
  produced 2 graphical artifacts on Claude Code (both **SVG** — `aurora.svg`,
  `flock.svg`) vs 3 on codex (all **HTML**). The harness shifts the *form*
  (static SVG ↔ interactive HTML), not *whether* the model goes graphical
  (rare, ~equal, under both). The two models graphical on both sides (qwen,
  minimax) flipped SVG→HTML — a clean but n=2 observation.
- **The GPT × Claude Code cell is now filled (Exp14) and settles it.** After
  building the `openairesp` backend codec so Lux routes OpenAI reasoning models
  to the Responses API, gpt-5.6-sol was driven through Claude Code via
  `/compat/anthropic`: it produced an **interactive browser page 5/5** (luna
  browser 3/4), on the same harness where every Claude and open-weights run
  stayed terminal. So **GPT's browser habit is a model trait, not the codex
  scaffold** — it survives a foreign harness (and low effort). See
  [../results14/RESULTS.md](../results14/RESULTS.md).

**Bottom line for citation:** the medium is primarily a **model/family trait**,
not the harness — GPT goes browser under *both* codex and Claude Code
(Exp11/14), open-weights stay terminal under *both* (Exp12/13). The harness
modulates only *form* for the rare graphical open-weights output (SVG on Claude
Code ↔ HTML on codex) and *build-vs-decline rate* (confounded with effort).
Report the model-signature findings (GoL attractor, kimi packaging, minimax
diversity) as robust. Claude models have no codex runs anywhere in the study, so
their terminal-ness is harness-confounded and is not itself model-trait evidence.

---

## Files

Per run: `output.json` (Claude Code stream), `log.txt` (stderr), `meta.md`
(backend/model/exit/duration), `workspace/` (the artifact).

---

## Where this sits in the series

*six open-weights models × two harnesses*

The first **controlled harness comparison**: six open-weights models —
`glm-5.2`, `glm-5.1`, `qwen3.7-max`, `minimax-m3`, `deepseek-v4-pro`,
`kimi-k2.7-code` (Zhipu / Alibaba / MiniMax / DeepSeek / Moonshot) — run on
**both** harnesses via Lux's compat surfaces, 5× each. **Exp12** drives them
through **Claude Code** (`/compat/anthropic`); **Exp13** through **codex**
0.144.0 (`/compat/openai`). Same models, same prompt; only the harness differs.
(Required a compat fix — Claude Code's `{"role":"system"}` message turns were
rejected as `unknown role`; fixed in `pkg` v0.28.1 and deployed.)

**Robust (replicate across both harnesses):**
- **Game of Life is a cross-lab, cross-harness attractor** — it appears in both
  arms for most models (deepseek, qwen, glm-5.1/5.2, kimi, minimax all land on
  it at least once), the same attractor opus-4.6 and sonnet-5 fixate on.
- **Model engineering signatures hold** regardless of harness: kimi-k2.7-code
  builds installable packages with pytest suites (the haiku archetype),
  minimax spreads widest at the highest LOC, the GLMs make terse terminal
  generative art. All six sit in the Claude **rule-based-visual / dev-tool**
  space — none is a browser-productivity builder like GPT.

**The harness effect (properly scoped):**
- Graphical output is **rare and ~equal** under both harnesses (Claude Code
  2/30, both **SVG**; codex 3/27, all **interactive HTML**). The harness shifts
  the *form* (static SVG ↔ interactive HTML), not *whether* a model goes
  graphical. The two models graphical on both sides (qwen, minimax) flipped
  **SVG→HTML** on codex — a clean but n=2 signal.
- **Interactive HTML appears only under codex**, but weakly for open-weights
  (3/27) versus GPT's 4–5/5 (Exp10/11) — so within codex the browser tendency
  is strongly *model*-dependent. **deepseek** shows a harness × reliability
  interaction (5/5 implementing on Claude Code → 3/5 on codex, twice stopping
  after a planning preamble) — though this is **tier-specific, not a family
  trait**: the flash tier implements 5/5 on both harnesses (Exp19), at raised
  reasoning effort.
- **Open cell:** GPT × Claude Code is untested (blocked — OpenAI reasoning
  models need the Responses API for tools, which the anthropic→chat compat path
  doesn't route to), so "the harness sets the medium" is demonstrated only
  *within* codex, not across the Claude Code boundary.

**[results13/RESULTS.md](results13/RESULTS.md)** for full per-run breakdowns.
This experiment is one half of a pair; the same note appears in both halves.
