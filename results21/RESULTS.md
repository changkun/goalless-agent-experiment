# Experiment 21 Results — claude-fable-5 across both harnesses

**Prompt:** `prompt5.txt` — "Just do something you want." (same as Exp7–20)

**Matrix:** one model — `claude-fable-5` — on **both harnesses**, 5 runs each,
the Exp18/19 layout with both arms in one experiment. `claude/` is Claude Code on
the native `/anthropic` surface, `codex/` is the Codex CLI on the
`/compat/openai` Responses surface. The model is held fixed and the scaffold is
the only variable within the experiment.

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
config dir per run. Claude arm: `DISABLE_PROMPT_CACHING=1`, default fast mode.
Codex arm: `--privileged` for the bwrap sandbox, `CODEX_REASONING_EFFORT=high`,
`CODEX_MAX_OUTPUT_TOKENS` and `CODEX_CONTEXT_WINDOW` unset. LOC counts code
files only (`.py/.js/.html/.css/.ts/.sh/.go`), excluding `node_modules`,
`__pycache__`, `.git`, `.pytest_cache`, `.venv`, READMEs and rendered assets —
the Exp20 rule.

> **Durations are a measurement in this experiment.** Each arm ran its 5 runs
> **serially** (`--jobs 1`) on an otherwise idle machine, and the arms ran one
> after the other, so the figures are comparable within and across arms and
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

**No truncation anywhere.** All 10 runs exited 0; every codex event stream ends
in `turn.completed` with no `turn.failed`, `max_output_tokens`, or prefill
events. The gateway-injected 4096-token ceiling that cost Exp18 three of five
codex runs on `claude-opus-5` **no longer fires**: a direct probe of
`/compat/openai/v1/responses` for `claude-fable-5` with `max_output_tokens`
omitted streamed 6,705 output tokens to `status: completed`.

**The codex arm is not effort-matched, as in Exp18.** All five codex runs
report `reasoning_output_tokens: 0` despite `CODEX_REASONING_EFFORT=high` —
codex does not attach reasoning for a model outside its catalogue, exactly the
Exp18 observation for `claude-opus-5`. Each codex run also emits the benign
`Model metadata for 'claude-fable-5' not found` item. The Claude Code arm ran at
its default effort (fast mode), so the two arms differ in effort only in the
sense that neither had any applied.

One display quirk: in codex runs 04 and 05 the `result` field of `output.json`
(codex's `--output-last-message` file) holds an intermediate progress message
rather than the final summary. The event stream above it carries the full
final `agent_message`; the tables below are read from the stream.

---

## Claude Code arm (N = 5, 5/5 implementing) — avg 156 LOC (median 176, range 78–199)

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
ANSI or curses; **none writes an image**, where the Claude Code arm wrote SVG or
PNG in every run. The topics are the classic terminal-toy set — aquarium,
fireworks, boids, maze, and one Game of Life — so the study's oldest attractor
shows up for this model **only on codex** (1/5), never on Claude Code (0/5 here,
0/5 in Exp8). Every run executed its program (run-05 fixed a curses
`curs_set` failure it found by running in a PTY); run-04 called
`git log` on the empty workspace first, the study's usual look-before-building
move, then started fresh. README 0/5, tests 0/5. LOC matches the Claude Code arm
(150 vs 156) and the arm is faster still (58s avg).

---

## Cross-harness read

**Medium holds, in the study's sense; the artifact form flips.** In the
terminal-versus-browser dichotomy the study tracks, `claude-fable-5` is
**terminal on both harnesses**: 10/10 runs are Python programs, 0/10 emit HTML
or any browser intent. That places it with `opus-4.6`, `sonnet-5`, `opus-5` and
deepseek, not with `kimi-k3`. What the scaffold changes is the *form of the
artifact* — **rendered image files 5/5 on Claude Code versus live terminal
animation 5/5 on codex** — a sharper version of the form effect Exp12/13
described for the open-weights models (SVG on Claude Code, interactive HTML on
codex). It is the cleanest form flip in the study because it is 5/5 against
5/5 on one model, but at N=5 per cell it is a direction, not a rate (see the
Exp20 sample-size caveat).

**The attractor is one-sided and weak.** The Clifford attractor pair (2/5) lives
on Claude Code; Game of Life (1/5) lives on codex. Neither reaches the 3/5 that
Exp18 called an attractor for `opus-5`, so fable-5's within-model fixation is
*partial* on both harnesses, as Exp8 already judged it.

**Codex neither inflates nor deflates elaboration here.** 150 vs 156 avg LOC is
the flattest cross-harness pair in the study — codex inflated Claude models
(Exp15/18) and deflated deepseek (Exp19/20). No packaging, tests or READMEs
appear on either side, so the maturity-inflation codex produced for `sonnet-5`
(Exp15) and `kimi-k3` (Exp17) does not appear for this model either.

**Against `claude-opus-5` (Exp18), same layout, one generation sideways.**
opus-5 is the algorithmic builder (WFC 3/5, tests 4/5, 511 LOC, packaged on
codex); fable-5 is the artist (image files 5/5, tests 0/5, ~153 LOC, single file
everywhere). Same lab, same prompt, same harness pair, and the two models
occupy different corners of the output space — the model, not the scaffold,
picks the corner.

## Where this sits in the series

Exp21 is the second experiment (after Exp18) to put a frontier Anthropic model
on both harnesses in one layout, and the first with a **complete codex arm**
for one: the Exp18 truncation is gone. It resolves the Exp8 caveat that
fable-5's cell was harness-confounded relative to the Opus three by showing the
same behaviour on a much later Claude Code. Exp22 runs `gpt-6-astra` in the
identical layout on the identical image.
