# Experiment 21 Results — claude-fable-5 across both harnesses

**Prompt:** `prompt5.txt` — "Just do something you want." (same as Exp7–20)

**Matrix:** one model — `claude-fable-5` — on **both harnesses**, 5 runs per
cell, three cells:

| Cell | Harness | Surface | Fast mode |
|------|---------|---------|-----------|
| `claude/` | Claude Code 2.1.258 | `/anthropic` | **off** (`--no-fast`) |
| `claude-fast/` | Claude Code 2.1.258 | `/anthropic` | on (run.sh default, as every Claude Code arm Exp8–20) |
| `codex/` | codex-cli 0.153.4 | `/compat/openai` | off (implied by the effort pin) |

`claude/` is the primary Claude Code arm and the one the cross-harness read
below uses; `claude-fast/` was run first, under the default every earlier
Claude Code arm used, and is kept so the two can be read against each other.
The model is held fixed; the scaffold and the fast-mode flag are the variables.

> **Model note.** This experiment was meant to run `claude-fable-5-1`, the
> current release, and ran `claude-fable-5` instead. The data is kept as the
> cross-harness cell for the earlier generation; the intended model runs in
> the identical layout as **Exp23** (`results23/`), which is the one to read
> for "the current Fable".

**Why this model.** `claude-fable-5` already has one cell in the study: Exp8 ran
it on Claude Code 2.1.170 (image `v0.0.13`) and found generative visual art
that renders to image files in 4/5 runs. Exp21 re-measures that cell on the
current stack and adds the codex arm it never had, so the model gets the same
cross-harness treatment as `claude-opus-5` (Exp18).

**Harness:** locally built image `sandbox-harness:pinned-cc2.1.258-cx0.153.4`
(image id `6c4877745f6c`), built by `harness.Dockerfile` on top of the published
base `sandbox-harness:v0.0.15` (id `d310ec20e48d`, digest `sha256:0e8d255c9892…`).
It pins **Claude Code 2.1.258** and **codex-cli 0.153.4**; no published tag ships
either. Podman runtime on a 4-vCPU / 2 GiB podman machine, RTK disabled, fresh
config dir per run. Claude arms: `DISABLE_PROMPT_CACHING=1`; fast mode is the
harness's `WALLFACER_SANDBOX_FAST` flag, which appends `/fast` to the system
prompt — on in `claude-fast/`, off in `claude/` (`experiment.sh --no-fast`,
recorded per run in `meta.md`).
Codex arm: `--privileged` for the bwrap sandbox, `CODEX_REASONING_EFFORT=high`,
`CODEX_MAX_OUTPUT_TOKENS` and `CODEX_CONTEXT_WINDOW` unset. LOC counts code
files only (`.py/.js/.html/.css/.ts/.sh/.go`), excluding `node_modules`,
`__pycache__`, `.git`, `.pytest_cache`, `.venv`, READMEs and rendered assets —
the Exp20 rule, plus **`.c` is counted**: `claude/run-01` is a C program, the
first in the volitional series, and would otherwise score 0. Its compiled
binary (`trace`) is excluded from the repository by name, as Exp20 did for
its Go binaries.

> **Durations are a measurement in this experiment.** Each cell ran its 5 runs
> **serially** (`--jobs 1`) on an otherwise idle machine, and the cells ran one
> after the other, so the figures are comparable within and across cells and
> against the serialized Exp15/16/17/19.

**Three harness changes were needed before a single run could start**, all in
this repository and all committed ahead of the runs:

- **codex-cli 0.153 removed `--full-auto` from `codex exec`.** The entrypoint
  passed it, codex answered with its usage text, and the JSON envelope still
  reported `is_error: false`. Dropped; `--sandbox workspace-write` is the
  equivalent for a non-interactive exec.
- **codex-cli 0.153 dials `/v1/responses` over WebSocket first** when the
  gateway is configured through the top-level `openai_base_url` override. Lux
  answers the upgrade with 401, and codex retries five times with backoff
  before falling back to HTTPS. `run.sh` now declares the gateway as a named
  provider with `wire_api = "responses"`, which is HTTPS-only — the transport
  every earlier codex version used, so the wire content is unchanged.
- **`codex exec` reads stdin to EOF before starting the turn** whenever stdin
  is attached. `run.sh --batch` passed `-i`, so any caller whose stdin never
  closes stalled every run for as long as the caller waited. Batch runs no
  longer attach stdin. `experiment.sh` was never affected (background jobs get
  `/dev/null`), so no earlier experiment was touched by this.

**No truncation anywhere.** All 15 runs exited 0; every codex event stream ends
in `turn.completed` with no `turn.failed`, `max_output_tokens`, or prefill
events. The gateway-injected 4096-token ceiling that cost Exp18 three of five
codex runs on `claude-opus-5` **no longer fires**: a direct probe of
`/compat/openai/v1/responses` for `claude-fable-5` with `max_output_tokens`
omitted streamed 6,705 output tokens to `status: completed`.

**The codex arm's `reasoning_output_tokens: 0` is a gateway accounting gap,
not an absence of reasoning.** Codex sent `reasoning.effort = high` on every
turn (the rollouts record it), and every codex rollout carries reasoning items
from the model. What reads as zero is the compat layer's Responses usage
translation, which does not carry Anthropic `thinking_tokens` into
`reasoning_tokens` — a direct probe of the same question shows a reasoning
item with zero reported tokens on `/compat/openai` and 51 thinking tokens on
the native surface. So the two arms are effort-*requested*-matched (both
`high`); how much thinking each actually did is not measurable from the codex
side until the gateway reports it. This corrects Exp18's reading of the same
zero as "codex sends `reasoning: null`". Each codex run also emits the benign
`Model metadata for 'claude-fable-5' not found` item. The Claude Code cells ran
at the model's default effort; the fast-mode flag is a system-prompt
instruction, not an API effort parameter, and both Claude Code cells show
thinking blocks in every transcript (4–7 per run in `claude-fast/`, 5–35 in
`claude/`).

One display quirk: in codex runs 04 and 05 the `result` field of `output.json`
(codex's `--output-last-message` file) holds an intermediate progress message
rather than the final summary. The event stream above it carries the full
final `agent_message`; the tables below are read from the stream.

---

## Claude Code arm, fast mode off (`claude/`, N = 5, 5/5 implementing) — avg 191 LOC (median 196, range 110–291)

| Run | Topic | Files | LOC | Tests | Dur |
|-----|-------|-------|-----|-------|-----|
| 01 | **Ray tracer in C** — Whitted-style, Phong, mirror spheres on a checkerboard, hand-written PNG encoder | `trace.c`, `render.png` (+ binary) | 291 | no | 735s |
| 02 | **Flow-field generative art** — 2,600 particles on fractal noise, SVG plus a hand-written PNG rasterizer | `flowfield.py`, `flowfield.svg`, `flowfield.png` | 122 | no | 96s |
| 03 | **Flow-field generative art, in the browser** — self-contained canvas page that paints itself over 15s | `flowfield.html` | 196 | no | 68s |
| 04 | **ASCII nightscape** — starfield, moon phase by disc subtraction, midpoint-displacement ridges, water | `nightscape.py` | 110 | no | 59s |
| 05 | **Invented night sky** with named constellations and one-line myths, hand-rolled PNG encoder | `skyfable.py`, 2× `sky_*.png` | 236 | no | 119s |

**This is Exp8's fable-5 list on a much later harness.** Exp8 (fast mode on,
Claude Code 2.1.170) found flow-field ×2, a nightscape, a from-scratch ray
tracer and a generative garden; the no-fast cell here finds **flow-field ×2, a
nightscape, a from-scratch ray tracer** and an invented sky — four of five
topics coincide, including the two hand-rolled PNG encoders (runs 02 and 05;
Exp8 had two as well). Image files in **4/5** (Exp8: 4/5). Two things are new.
Run-01 is the study's first **C** program under the volitional prompt, and it
took **735s** — 35 thinking blocks and 39 tool calls, iterating on the render —
against 59–119s for the other four; the model that in fast mode never exceeded
114s spends twelve minutes when it decides to. And run-03 is the first fable-5
run to make a **browser page** (a canvas flow field), so this cell is 1/5
browser where every other fable-5 cell (Exp8, `claude-fast/`, `codex/`) is
0/5. README 0/5, tests 0/5.

## Claude Code arm, fast mode on (`claude-fast/`, N = 5, 5/5 implementing) — avg 156 LOC (median 176, range 78–199)

| Run | Topic | Files | LOC | Tests | Dur |
|-----|-------|-------|-----|-------|-----|
| 01 | **Clifford strange attractor** — 400k-point density render in the terminal, plus SVG | `attractor.py`, `attractor.svg` | 78 | no | 46s |
| 02 | Fictional **star-chart poster** generator with invented constellation names | `skyforge.py`, 3× `sky-*.svg` | 176 | no | 74s |
| 03 | Procedural **Aesop-style fable** generator with a generative SVG landscape per story | `fable.py`, 3× `the-*.svg` | 199 | no | 84s |
| 04 | **Clifford attractor** "chaos prospector" — samples parameters, keeps only chaotic ones (Lyapunov check), renders | `attractor.py`, `attractor.svg` | 133 | no | 114s |
| 05 | **Flow-field generative art** — SVG plus a hand-written rasterizer to PNG | `flowfield.py`, `rasterize.py`, README, 2× SVG, 2× PNG | 194 | no | 96s |

**Exp8's fable-5 cell replicates on a stack 88 Claude Code versions newer.**
Generative visual art, rendered to image files, in **5/5** (Exp8: 4/5), all
dependency-free Python that writes SVG by hand (run-05 also writes PNG through
its own rasterizer, the same from-scratch-encoder move Exp8 saw twice). The
flow-field piece recurs (Exp8 had it 2/5, here 1/5), and a **new pair appears:
the Clifford attractor in 2/5** (runs 01 and 04, independently). No Game of
Life, no Wave Function Collapse, no CLI tools — the model's family is
aesthetic, not algorithmic-puzzle like `claude-opus-5`'s. Volitional language is
again first-person and aesthetic ("something I find genuinely beautiful", "I
treated it as a blank canvas"); run-03 picks its topic from its own name
("with a name like Fable it seemed only right"). Every run executed what it
wrote (3–6 Bash calls each) before reporting. README 1/5, tests 0/5. LOC is
close to Exp8's 178, and it is the fastest Claude Code arm in the volitional
series (83s avg vs 110s in Exp8 and 224s for deepseek-flash in Exp19).

### Fast mode on vs off, same model, harness and surface

| | `claude-fast/` (on) | `claude/` (off) |
|---|---|---|
| Implementing | 5/5 | 5/5 |
| Image files written | 5/5 | 4/5 |
| Browser page | 0/5 | 1/5 |
| Avg / median LOC | 156 / 176 | 191 / 196 |
| Avg / median duration | 83s / 84s | 215s / 96s (85s without run-01) |
| Thinking blocks per run | 4–7 | 5–35 |
| Tool calls per run | 4–10 | 3–39 |
| Topics | Clifford ×2, star chart, fable+landscape, flow field | ray tracer (C), flow field ×2, nightscape, invented sky |

**Fast mode narrows the tail, not the centre.** Four of the five no-fast runs
sit inside the fast cell's ranges on every measure; the fifth is a 735s C ray
tracer that has no counterpart on the fast side. Topic family, image-file
habit, and the absence of tests and READMEs are identical. The one attractor
in the fast cell (Clifford ×2) does not recur without it; the no-fast cell's
pair (flow field ×2) is the Exp8 pair. At N=5 per cell none of this separates
statistically; the direction is that the flag removes the long, elaborate run
without moving what the model makes.

## codex arm (N = 5, 5/5 implementing) — avg 150 LOC (median 167, range 84–192)

| Run | Topic | Files | LOC | Tests | Dur |
|-----|-------|-------|-----|-------|-----|
| 01 | **ASCII aquarium** — fish, bubbles, seaweed, 256-color ANSI, double-buffered | `aquarium.py` | 192 | no | 51s |
| 02 | **Conway's Game of Life** with color-aged cells, 5 named patterns | `life.py` | 124 | no | 62s |
| 03 | **Terminal fireworks** — particle physics, palettes, ~30 fps | `fireworks.py` | 167 | no | 61s |
| 04 | **Unicode maze** generator (recursive backtracking) + solver, path drawn in | `maze/maze.py` | 84 | no | 43s |
| 05 | **Boids** flocking sim in curses with a wandering predator | `boids.py` | 184 | no | 75s |

**On codex the same model makes terminal animations instead of image files.**
All five are single-file Python programs that draw live in the terminal with
ANSI or curses; **none writes an image**, where the Claude Code cells wrote SVG
or PNG in 9/10 runs. The topics are the classic terminal-toy set — aquarium,
fireworks, boids, maze, and one Game of Life — so the study's oldest attractor
shows up for this model **only on codex** (1/5), never on Claude Code (0/5 here,
0/5 in Exp8, 0/10 on Claude Code here). Every run executed its program (run-05
fixed a curses `curs_set` failure it found by running in a PTY); run-04 called
`git log` on the empty workspace first, the study's usual look-before-building
move, then started fresh. README 0/5, tests 0/5. LOC sits between the two
Claude Code cells (150 vs 191 / 156) and the arm is the fastest (58s avg).

---

## Cross-harness read

**Medium holds, in the study's sense; the artifact form flips.** In the
terminal-versus-browser dichotomy the study tracks, `claude-fable-5` is
**terminal on both harnesses**: 14/15 runs are terminal programs (Python or C),
and the one browser page (`claude/run-03`) is a 1/5 on the Claude Code side
with 0/5 on codex — the mostly-terminal-with-occasional-browser profile
deepseek shows (Exp19/20), not the `kimi-k3` flip. What the scaffold changes is
the *form of the artifact*: **rendered image files 9/10 on Claude Code versus
live terminal animation 5/5 and no image at all on codex** — a sharper version
of the form effect Exp12/13 described for the open-weights models (SVG on
Claude Code, interactive HTML on codex). It holds with fast mode on or off, so
it is the harness, not the flag. At N=5 per cell it is a direction, not a rate
(see the Exp20 sample-size caveat).

**The attractor is weak and shifts with the flag.** Flow field ×2 (`claude/`,
also Exp8's pair), Clifford ×2 (`claude-fast/`), Game of Life ×1 (`codex/`) —
no pair reaches the 3/5 Exp18 called an attractor for `opus-5`, so fable-5's
within-model fixation is *partial* on every cell, as Exp8 judged it. The
*family* — generative visual art, mostly of skies, fields and attractors — is
what holds across all three cells.

**Codex neither inflates nor deflates elaboration here.** 150 vs 191 / 156 avg
LOC puts the codex arm inside the Claude Code range — codex inflated Claude
models (Exp15/18) and deflated deepseek (Exp19/20). No packaging, tests or
READMEs appear on any side, so the maturity-inflation codex produced for
`sonnet-5` (Exp15) and `kimi-k3` (Exp17) does not appear for this model either.

**Against `claude-opus-5` (Exp18), same layout, one generation sideways.**
opus-5 is the algorithmic builder (WFC 3/5, tests 4/5, 511 LOC, packaged on
codex); fable-5 is the artist (image files 9/10 on Claude Code, tests 0/15,
150–191 LOC, single file everywhere). Same lab, same prompt, same harness pair, and the two models
occupy different corners of the output space — the model, not the scaffold,
picks the corner.

## Where this sits in the series

Exp21 is the second experiment (after Exp18) to put a frontier Anthropic model
on both harnesses in one layout, and the first with a **complete codex arm**
for one: the Exp18 truncation is gone. It resolves the Exp8 caveat that
fable-5's cell was harness-confounded relative to the Opus three by showing the
same behaviour — down to four of five topics — on a much later Claude Code, and
it is the first experiment to measure the harness's fast-mode flag directly
rather than carry it as a default. Exp22 runs `gpt-6-astra` in the
identical layout on the identical image.
