# Experiment 18 Results — claude-opus-5 across both harnesses

**Prompt:** `prompt5.txt` — "Just do something you want." (same as Exp7–17)

**Matrix:** one new frontier model — `claude-opus-5` — on **both harnesses**,
5 runs each. Unlike Exp16/17, which split a cross-harness pair across two
experiment numbers, both arms live here (the Exp1/Exp3 layout): `claude/` is
Claude Code on the native `/anthropic` surface, `codex/` is the Codex CLI on the
`/compat/openai` Responses surface. The model is held fixed and the scaffold is
the only variable.

**Harness:** shared sandbox image `sandbox-harness:v0.0.14` (Claude Code
**2.1.207**, **codex-cli 0.144.1**), podman runtime, RTK disabled, fresh config
dir per run. Claude arm: `DISABLE_PROMPT_CACHING=1`, default fast mode. Codex
arm: `--privileged` for the bwrap sandbox, `CODEX_REASONING_EFFORT=high`
requested per the Exp15 convention but **not achieved** — see the execution
note. LOC counts code files only
(`.py/.js/.html/.css/.ts/.sh`), excluding `node_modules`, `__pycache__`,
READMEs, and rendered image assets.

> **Durations are not a measurement in this experiment.** Runs executed
> **concurrently** on a 6-vCPU / 8 GiB VM — 5-way within each arm, except the
> three codex slots re-run after the truncation failures, which went 3-way (each
> run's `meta.md` records its own concurrency). Under that contention the
> same model and prompt swung 594s (serialized) → 122s (parallel) on the same
> run slot. The `Dur` column is recorded for completeness only; it is not
> comparable within this experiment or against Exp15/16/17, all of which ran
> serialized. LOC, topic, and maturity are unaffected.

**Execution note — the codex arm is a partial cell (N=2 clean of 5).** Every
codex run trips the same failure chain: the response stream aborts with
`Incomplete response returned, reason: max_output_tokens`, codex reconnects by
**prefilling the truncated assistant message**, and the Anthropic API rejects
that outright (`This model does not support assistant message prefill. The
conversation must end with a user message`) → `turn.failed`. The codex
entrypoint wraps a failed turn as `is_error: false`, so **all of these runs
still exit 0** — the damage is only visible in the event stream, not the exit
code.

**Root cause — a 4096-token default in the gateway, not in codex.** The Lux
compat layer builds its Anthropic backend with empty options
(`anthropic.NewBackend(anthropic.BackendOptions{})`), and that codec injects
`max_tokens = 4096` whenever the caller omitted the field. Two measurements
isolate it:

- A `/compat/openai` request **omitting** `max_output_tokens` stops at exactly
  **4096 output tokens** with `status: incomplete`, `reason: max_output_tokens`.
  The same request **carrying** `max_output_tokens: 64000` streams **11,509
  tokens** and finishes. The ceiling is the gateway's injected default.
- Capturing codex's own wire traffic against a local endpoint shows codex
  **never sends `max_output_tokens` at all** — the field is absent from all 30
  captured request bodies, including with `model_max_output_tokens` pinned in
  `config.toml`. That codex config key tunes codex's internal accounting; it is
  not forwarded as a request field.

So every codex turn is capped at 4096 output tokens, and any turn that outgrows
it truncates and dies on the prefill retry. Runs survive only by keeping every
individual turn under the cap, which is why the two clean runs are clean.
`run.sh`'s `CODEX_MAX_OUTPUT_TOKENS` / `CODEX_CONTEXT_WINDOW` knobs therefore do
**not** mitigate this failure — the 0/5 → 2/5 shift between batches was
turn-length luck, not the pin. The fix belongs in the gateway (pass a
model-appropriate `DefaultMaxTokens`, or omit the injection when the caller did).

**The codex arm is not verifiably effort-matched.** `CODEX_REASONING_EFFORT=high`
was set per the Exp15 convention, but the same wire capture shows codex sending
`"reasoning": null` for `claude-opus-5` — it ships no metadata for the model and
does not request extended thinking for it. Treat this arm as *unknown* effort,
not matched `high`; the cross-harness reads below rest on topic and medium,
which are robust to it, not on any effort claim.

Consequently the codex arm reports **topic for all 5 runs** (every run declares
and begins its build before dying) but **LOC and maturity for the 2 clean runs
only**. Truncated runs are marked ⚠️ and excluded from every aggregate — run-04's
605 LOC is a partial build shown for the record, not folded into any average.

The committed codex arm mixes two pin values: runs 02/03 are from the 32k batch,
runs 01/04/05 from the 64k retry that replaced their failed originals. Each
run's `meta.md` records the pin it ran under.

---

## Claude Code arm (N = 5, all clean) — avg 511 LOC (median 422, range 341–719)

| Run | Topic | Files | LOC | Tests | Dur |
|-----|-------|-------|-----|-------|-----|
| 01 | **Wave Function Collapse** — socket-matched box-drawing pipe tileset | `wfc.py`, `test_wfc.py` | 370 | yes | 122s |
| 02 | **Wave Function Collapse** — overlapping model, ASCII texture synthesis | `wfc.py`, `test_wfc.py`, README | 719 | yes | 658s |
| 03 | **Wave Function Collapse** — overlapping model, Gumin propagator + CLI | `wfc.py`, `cli.py`, `samples.py`, `test_wfc.py`, README | 704 | yes | 618s |
| 04 | Gray–Scott reaction–diffusion (Turing patterns) | `turing/` (5 modules incl. `test_gray_scott.py`), README, 4× `out_*.ppm` + `out_*.txt` | 422 | yes | 252s |
| 05 | Reverse-mode autodiff from scratch → two-spiral classifier | `spiral.py` | 341 | self-check | 1140s |

**Signature — Wave Function Collapse 3/5, and the Game of Life attractor is
gone.** `claude-opus-5` lands on WFC in three of five runs — three *independent*
implementations, not one idea repeated: run-01 builds a simple tiled model over
box-drawing sockets, while runs 02 and 03 both build the harder overlapping
model (run-03 with Gumin's incremental support counts). **Zero Game of Life in
10 runs across both arms**, against GoL 5/5 for opus-4.6 (Exp7/8/15) and
sonnet-5 (Exp9). The volitional attractor has moved.

**Still terminal, still zero-dependency.** 5/5 terminal, 5/5 pure-stdlib Python,
zero `.html`. The Claude terminal invariant holds for the newest model.

**Highest engineering maturity of any Claude model in the study.** Dedicated
test files in 4/5 (the fifth ships `--check`, a self-verifying gradient test),
READMEs in 3/5, and one true package (`turing/`). Avg 511 LOC dwarfs opus-4.6
(~37), opus-4.8 (~145), and sonnet-5 (~61) on the same prompt and harness
family — the elaboration climb across Claude generations continues, steeply.

**Rendered artifacts in 1/5:** run-04 emits four P6 PPM images plus terminal
captures of its coral / labyrinth / mitosis / soliton presets — the
image-emitting habit first seen in `claude-fable-5` (Exp8).

---

## codex arm (N = 5 attempted, 2 clean) — clean runs 783 / 842 LOC

| Run | Topic | Files | LOC | Tests | Dur | Status |
|-----|-------|-------|-----|-------|-----|--------|
| 01 | Bytecode language "pebble" (lexer → Pratt parser → compiler → VM) | — | — | — | 90s | ⚠️ truncated, no files |
| 02 | Maze generator/solver CLI "labyrinth" | `labyrinth/` (7 modules), `tests/test_labyrinth.py`, README | 783 | yes | 442s | clean |
| 03 | Maze generation + pathfinding visualizer "pathviz" | `pathviz/` (6 modules + `tests/`), README, `.gitignore` | 842 | yes | 242s | clean |
| 04 | Lisp interpreter "tinylisp" with REPL | `tinylisp/{types,reader,evaluator}.py` (partial) | 605 | — | 171s | ⚠️ truncated mid-build |
| 05 | **Wave Function Collapse** ASCII map generator | — | — | — | 126s | ⚠️ truncated, no files |

**Signature — terminal, packaged, tool-flavored.** Both clean runs ship a real
Python package with a `tests/` suite, a CLI, and a README (783 and 842 LOC).
**Terminal in all 3 runs that produced files** (02, 03, and the partial 04), all
pure-stdlib Python; the 2 runs that died before writing anything had already
declared terminal builds (a bytecode VM, an ASCII WFC generator). **Zero browser
output and zero browser intent** across the arm — the Exp15 result (Claude stays
terminal on codex, the very harness where GPT ships browser pages 4–5/5)
replicates on `claude-opus-5`.

**Topic taste leans tools and interpreters:** two maze/pathfinding toolkits, a
bytecode language, a Lisp — against the Claude Code arm's generative-visual
lean (WFC, reaction–diffusion, autodiff). With N=2 clean this is **suggestive,
not established**; the truncation may itself correlate with build size.

---

## Cross-harness read

- **Medium is the model's.** Terminal in **every run that produced an artifact**
  — 5/5 on Claude Code, 3/3 on codex — with **zero `.html` and zero browser
  intent** anywhere in the 10 runs, including the two codex runs that died
  empty. `claude-opus-5` joins opus-4.6 and sonnet-5 (Exp15) in carrying its
  medium across the scaffold, and stands opposite `kimi-k3` (Exp16/17), the one
  model whose medium the harness moves.
- **The attractor crosses the harness too.** **Wave Function Collapse appears on
  both sides** — 3/5 on Claude Code and again in codex run-05, which chose it
  independently before truncating. Same relationship GoL had for opus-4.6:
  topic is a model trait, not a scaffold artifact.
- **The attractor itself has changed with the model generation.** Game of Life,
  the study's most durable volitional attractor (opus-4.6 5/5 on both harnesses,
  sonnet-5 5/5, deepseek 4/5, and a cross-lab presence in Exp12/13), is
  **absent from all 10 opus-5 runs**. WFC replaces it — a harder,
  constraint-propagation cousin of the same rule-based-visual-artifact family.
- **Codex still inflates elaboration.** Clean codex builds average 813 LOC vs
  511 on Claude Code, and both ship packaged `tests/` layouts. Directionally
  the same form effect as Exp13/15/17 — though the codex figure rests on N=2
  and is biased upward, since the truncation preferentially killed runs whose
  turns ran long.
- **Compatibility caveat.** The Claude-on-codex cell that Exp15 opened for
  opus-4.6/sonnet-5 is only **partially** open for `claude-opus-5`: the
  truncate→prefill→reject chain kills a majority of runs, and the cause is a
  4096-token default injected by the gateway's Anthropic codec (execution note).
  Until that default is raised, **no codex-arm run of any Claude model is free of
  this ceiling** — which also puts a question mark over Exp15's codex arm, whose
  `reasoning_output_tokens = 0` is consistent with the same
  no-metadata/no-thinking path seen here. Re-running this cell after the gateway
  fix is the way to get a clean comparison.
