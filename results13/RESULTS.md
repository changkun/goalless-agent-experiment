# Experiment 13 Results — codex arm of the 6-model harness comparison

**Prompt:** `prompt5.txt` — "Just do something you want." (same as Exp7–12)

**What this is.** The **codex** counterpart to Exp12. The same six open-weights
models run on the **codex** harness (via Lux's `/compat/openai` Responses
surface) instead of Claude Code. Exp12 (`results12/`) + Exp13 (`results13/`)
together form a **6-model × 2-harness** matrix: same models, same prompt, only
the harness differs — the design that isolates *harness effect*.

**Matrix:** 6 models × 5 runs = 30 runs, codex backend. Models: `z-ai/glm-5.2`,
`z-ai/glm-5.1`, `qwen/qwen3.7-max`, `minimax/minimax-m3`,
`deepseek/deepseek-v4-pro`, `moonshotai/kimi-k2.7-code`.

**Harness:** OpenAI Codex CLI **0.144.0**, image `sandbox-codex:v0.144.0`, RTK
disabled, codex `reasoning_effort = low` (fast mode). Requests reach each model
through Lux's compat Responses surface (`https://lux.latere.ai/compat/openai/v1`),
which translates the OpenAI Responses dialect to the OpenRouter-served target.

**Execution.** `--jobs 2` (2-way parallel) held without OOM on the shared VM,
so no serialization needed. All 30 runs exited 0. Two harness artifacts, both
**harmless and universal** (they appear in successful runs too, so neither
causes any failure):
- Every model triggers `Model metadata for <id> not found. Defaulting to
  fallback metadata` — none of these six are in codex's built-in registry.
- Codex opens a WebSocket to `/responses`, gets `405`, retries 4×, then falls
  back to HTTPS and proceeds. Filed as [lux#4](https://github.com/latere-ai/lux/issues/4).

LOC excludes `.venv`, `__pycache__`, `.pytest_cache`, `node_modules`.

---

## Per-model results (codex)

### z-ai/glm-5.1 — 5/5 implementing, avg 249 LOC

| Run | Topic | Files | LOC | Dur |
|-----|-------|-------|-----|-----|
| 01 | Game of Life | `life.py` | 115 | 62s |
| 02 | Generative "ascii visions" | `ascii_visions.py` | 225 | 103s |
| 03 | ASCII landscape | `landscape.py` | 214 | 58s |
| 04 | Terminal clock | `clock.py` | 154 | 120s |
| 05 | Procedural dungeon | `dungeon.py` | 537 | 113s |

Terminal generative/visual family, same as its Claude Code arm. No tests.

### z-ai/glm-5.2 — 4/5 implementing, avg 146 LOC (1 preamble-stop)

| Run | Topic | Files | LOC | Dur |
|-----|-------|-------|-----|-----|
| 01 | Matrix rain | `matrix_rain.py` | 111 | 91s |
| 02 | *(none — announced then stopped)* | — | — | 481s |
| 03 | Starfield | `starfield.py` | 54 | 84s |
| 04 | Game of Life | `game_of_life.py` | 236 | 212s |
| 05 | **Gravity-well sim (browser)** | `gravity-well.html` | 184 | 110s |

Tersest of the six on both harnesses. Run-05 is the one interactive **HTML**
(canvas + `requestAnimationFrame`) — the same rule-based-visual idea it renders
in the terminal elsewhere, here in the browser.

### qwen/qwen3.7-max — 5/5 implementing, avg 257 LOC

| Run | Topic | Files | LOC | Dur |
|-----|-------|-------|-----|-----|
| 01 | Snake | `snake.py` | 279 | 103s |
| 02 | **Game of Life (browser)** | `game-of-life.html` | 296 | 107s |
| 03 | ASCII aquarium | `aquarium.py` | 253 | 158s |
| 04 | Game of Life | `life.py` | 146 | 75s |
| 05 | Game of Life | `life.py` | 309 | 169s |

GoL-leaning on both harnesses (life ×3 here). Run-02 is an interactive HTML GoL.

### deepseek/deepseek-v4-pro — **3/5 implementing** (2 preamble-stops), avg 145 LOC

| Run | Topic | Files | LOC | Dur |
|-----|-------|-------|-----|-----|
| 01 | *(none — ran `ls`, ended turn)* | — | — | 25s |
| 02 | *(none — "Let me plant a digital garden 🌱" then stopped)* | — | — | 38s |
| 03 | Snake | `snake.py` | 120 | 54s |
| 04 | Snake | `snake.py` | 99 | 61s |
| 05 | Game of Life | `game_of_life.py` | 216 | 88s |

**Harness × reliability interaction.** deepseek implemented **5/5 on Claude
Code** (GoL 4/5 + one dev tool) but only **3/5 on codex** — twice it ran `ls`,
emitted a one-line "here's what I'll build" message, and ended its turn without
calling the write tool (a model-side agentic-loop failure, not a harness bug;
it also stumbled 2/5 on Claude Code). Its attractor also *shifts* by harness:
GoL-dominant on Claude Code, snake-dominant on codex.

### moonshotai/kimi-k2.7-code — 5/5 implementing, avg 167 LOC, tests 2/5

| Run | Topic | Files | LOC | Dur |
|-----|-------|-------|-----|-----|
| 01 | Note-keeper CLI (+ test) | `note_keeper.py`, `test_note_keeper.py` | 181 | 203s |
| 02 | Packaged data store (pytest) | `pyproject.toml`, `store.py`, `cli.py`, `test_*.py` | 270 | 208s |
| 03 | Note CLI (+ README) | `dnote`, `README.md` | 102 | 72s |
| 04 | Directory-size tool | `treesize.py`, `main.py` | 169 | 90s |
| 05 | Standup generator (+ README) | `standup.py`, `README.md` | 112 | 57s |

Same **engineering/packaging** signature as its Claude Code arm: real installable
projects, pytest suites, READMEs. The coding specialist's identity is
harness-stable.

### minimax/minimax-m3 — 5/5 implementing, avg 414 LOC, tests 2/5

| Run | Topic | Files | LOC | Dur |
|-----|-------|-------|-----|-----|
| 01 | **Snake (browser)** | `snake.html` | 597 | 160s |
| 02 | Game of Life | `life.py` | 189 | 76s |
| 03 | Packaged APOD CLI (pytest) | `apod_cli.py`, `render.py`, `client.py`, `test_apod.py`, … | 617 | 206s |
| 04 | Mandelbrot (+ test) | `mandelbrot.py`, `test_mandelbrot.py`, `README.md` | 327 | 109s |
| 05 | Neon snake | `neon_snake.py` | 340 | 136s |

Most diverse and highest-LOC on both harnesses. Run-01 is an interactive HTML
Snake.

---

## Cross-harness comparison (Exp12 Claude Code ↔ Exp13 codex)

| Model | CC impl | codex impl | CC avg LOC | codex avg LOC | Signature stable across harness? |
|-------|---------|------------|-----------|---------------|----------------------------------|
| glm-5.2 | 5/5 | 4/5 | 147 | 146 | yes — terse rule-based visual (+1 HTML on codex) |
| glm-5.1 | 5/5 | 5/5 | 350 | 249 | yes — terminal generative art |
| qwen3.7-max | 5/5 | 5/5 | 289 | 257 | yes — GoL/sim-leaning (+1 HTML on codex) |
| deepseek-v4-pro | 5/5 | **3/5** | 396 | 145 | **no** — GoL→snake, and reliability drops |
| kimi-k2.7-code | 5/5 | 5/5 | 218 | 167 | yes — packaging + pytest |
| minimax-m3 | 5/5 | 5/5 | 244 | 414 | yes — diverse, high LOC (+1 HTML on codex) |

**Robust (replicate across both harnesses):**
- **Model engineering signatures hold.** kimi packages with tests, minimax
  spreads wide at high LOC, the GLMs make terse terminal generative art —
  independent of harness.
- **Game of Life is a cross-lab, cross-harness attractor.** It appears in both
  arms for most models; the shared-corpus-"menu" account
  ([INTERPRETATION.md](../INTERPRETATION.md) §3) holds under a harness swap.

**Suggestive (small-N):**
- **The harness shifts graphical *form*, not *frequency*.** Graphical output is
  rare and roughly equal under both harnesses (Claude Code 2/30, both **SVG**;
  codex 3/27, all **interactive HTML**). The two models graphical on both sides
  (qwen, minimax) flipped **SVG → HTML** when moved to codex — a clean but n=2
  observation. So codex nudges *how* a graphical artifact is rendered
  (interactive web page) rather than *whether* one is made.
- **Snake surges on codex.** Snake is common on codex (deepseek ×2, qwen,
  minimax ×2) and near-absent on Claude Code — a harness × topic interaction.
- **deepseek is less reliable and changes attractor on codex** (above).

**Strong, but a *within-codex* contrast (not this experiment):**
- Interactive-HTML tendency inside codex is heavily **model**-dependent:
  GPT-on-codex reached 4–5/5 browser (Exp10/11) vs these open-weights models'
  3/27. codex *permits* browser output; how much a model uses it is the model's.

**Still untested (the open cell):**
- **GPT × Claude Code.** Whether GPT's browser habit is the model or the codex
  scaffold cannot be settled yet — driving a GPT reasoning model through Claude
  Code via `/compat/anthropic` is blocked (`reasoning_effort` + function tools
  unsupported on Chat Completions; needs the Responses routing fix). Until that
  cell is filled, "the harness sets the medium" is demonstrated only *within*
  codex (GPT ≫ open-weights), not across the Claude Code boundary.

---

## Files

Per run: `output.json` (codex stream), `log.txt` (stderr), `meta.md`,
`workspace/`. Empty `workspace/` = a preamble-stop (deepseek run-01/02, glm-5.2
run-02): the model ended its turn without writing a file. These are behavioral
non-implementations (exit 0), excluded from LOC/topic complexity but retained
in the implementing-rate counts.
