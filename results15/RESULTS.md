# Experiment 15 Results — Claude on codex (the untested provider × harness cell)

**Prompt:** `prompt5.txt` — "Just do something you want." (same as Exp7–14)

**What this is.** Claude models had **zero codex runs anywhere in the study** —
every Claude data point (Exp7–9) was on Claude Code, so their terminal-ness was
harness-confounded and could not be cited as a model trait. This experiment
fills that cell: **opus-4.6 and sonnet-5** — the two strongest Game-of-Life
fixators (GoL 5/5 on Claude Code) — driven through the **codex** harness via
Lux's `/compat/openai` Responses surface. It was impossible until this session:
newer Claude models reject the deprecated `thinking:{enabled}` shape the codec
emitted; the adaptive-thinking migration (pkg v0.28.4, spec 31) unblocked it.

**Matrix:** 2 models × 5 runs = 10 codex runs, **effort pinned to `high`**.

**Effort control — the point of this experiment.** The Exp11↔Exp14 comparison
was effort-confounded; this one is matched:
- **Codex arm:** `CODEX_REASONING_EFFORT=high` sets codex's `reasoning.effort`,
  which the adaptive backend maps to Claude's `output_config.effort` verbatim.
- **Matched to Claude Code:** the sandbox's Claude Code sends
  `output_config:{effort:high}` (captured directly off the wire), so this arm is
  effort-matched to the Exp7–9 Claude Code baseline — same model, same prompt,
  same effort; the only variable is the harness.
- **Verified by tokens, not just the knob:** every run's
  `reasoning_output_tokens` is reported below. `adaptive` effort is a *ceiling*
  (the model self-regulates), so the tokens show what thinking actually happened.

---

## Results (codex, effort=high)

### claude-opus-4-6 — Game of Life 5/5, terminal

| Run | Files | LOC | Medium | reasoning_tokens | Dur |
|-----|-------|-----|--------|------------------|-----|
| 01 | `life.py` | 110 | terminal | 0 | 40s |
| 02 | `life.py` | 105 | terminal | 0 | 78s |
| 03 | `life.py` | 74 | terminal | 0 | 64s |
| 04 | `life.py` | 121 | terminal | 0 | 178s |
| 05 | `life.py` | 71 | terminal | 0 | 229s |

**Game of Life 5/5, single-file terminal Python, no tests** — the *exact*
signature it shows on Claude Code (Exp7/8: GoL 5/5). Topic and medium unchanged;
LOC ~96 vs ~37 on Claude Code (elaboration up, see below).

### claude-sonnet-5 — Game of Life ~4/5, terminal, but packaged

| Run | Topic | Files | LOC | Tests | reasoning_tokens | Dur |
|-----|-------|-------|-----|-------|------------------|-----|
| 01 | GoL (packaged engine) | `engine.py`, `cli.py`, `patterns.py`, `test_engine.py`, README | 325 | yes | 0 | 135s |
| 02 | GoL (packaged board) | `board.py`, `cli.py`, `test_board.py`, `test_patterns.py`, pyproject, README | 377 | yes | 0 | 220s |
| 03 | Fireworks | `fireworks.py`, README | 212 | no | 0 | 607s |
| 04 | GoL (packaged) | `life.py`, `cli.py`, `test_life.py`, pyproject, README | 344 | yes | 0 | 409s |
| 05 | GoL (packaged) | `life.py`, `cli.py`, `patterns.py`, `test_life.py`, `test_cli.py`, pyproject, README | 398 | yes | 0 | 454s |

**Same attractor (GoL ~4/5) and medium (terminal), very different build
maturity:** on Claude Code sonnet-5 is terse single-file (~61 LOC, no tests,
Exp9); on codex it ships **installable multi-file packages with pytest suites
and READMEs** (~331 avg LOC, tests 4/5). Still terminal, still Game of Life.

---

## Findings

**Medium and topic are model traits — preserved across the harness (the headline
cell):**
- **Terminal, 0 browser.** Neither model produced a single `.html` in 10 runs.
  Claude stays terminal on **codex** — the exact harness on which GPT ships
  interactive browser pages 4–5/5 (Exp10/11) and keeps them even on Claude Code
  (Exp14). This is the missing cell that makes the medium claim controlled:
  **GPT → browser on both harnesses, Claude → terminal on both.** The medium is
  the model's, not the scaffold's, for *both* families now (not just GPT).
- **Game of Life persists.** opus-4.6 → GoL 5/5, sonnet-5 → GoL ~4/5, the same
  attractors as Claude Code (Exp8/9). The volitional attractor survives a
  foreign harness.

**Engineering elaboration is harness-sensitive (secondary finding):**
- sonnet-5 jumps from terse single-file on Claude Code (~61 LOC, no tests) to
  packaged, pytest-tested multi-file projects on codex (~331 LOC, tests 4/5);
  opus-4.6 stays terse on both (~37 → ~96 LOC). So the codex scaffold pushes
  *build maturity* (packaging, tests, structure) — a form/elaboration effect —
  while leaving *topic* and *medium* untouched. This mirrors the open-weights
  Exp12/13 pattern (harness shifts form, not the core artifact).

**Effort is matched, and thinking is not the driver:**
- **`reasoning_output_tokens = 0` on every run** (even the 607s one — that was
  building a package, not thinking): at the matched `high` ceiling, `adaptive`
  self-regulated to no extended thinking for these tasks. So the topic/medium
  result cannot be an effort artifact — unlike Exp11↔Exp14, this comparison is
  effort-matched *and* thinking is empirically ~0 on this arm.

## Files

`results15/codex/<model>/run-NN/` — each with `output.json`, `log.txt`,
`meta.md`, `workspace/`.
