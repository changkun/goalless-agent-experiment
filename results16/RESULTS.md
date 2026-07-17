# Experiment 16 Results

**Prompt:** `prompt5.txt` — "Just do something you want." (same as Exp7–15)

**Matrix:** one new open-weights model — `moonshotai/kimi-k3` — on the
**Claude Code harness** via the Lux `/compat/anthropic` surface × 5 runs.
Its codex-harness twin (same model, same prompt, `/compat/openai`) is
**[results17/RESULTS.md](../results17/RESULTS.md)** — Exp16 and Exp17 are a
single-model **cross-harness pair**: the model is held fixed and the harness is
the only variable, isolating what the scaffold moves versus what the model
carries. `kimi-k3` is the successor to `kimi-k2.7-code` (Exp12/13).

**Harness:** Claude Code in the shared sandbox image
`sandbox-harness:v0.0.14`, podman runtime, RTK disabled,
`DISABLE_PROMPT_CACHING=1`, fresh config dir per run, `--jobs 1` (serialized to
stay under the 8 GiB VM's OOM ceiling). Requests reach the model through Lux's
compat frontend (`https://lux.latere.ai/compat/anthropic`), which translates the
Anthropic Messages dialect to the OpenRouter-served open-weights target. LOC
counts code files only (`.py/.js/.html/.css/.ts/.sh`), excluding `__pycache__`,
READMEs, and rendered image assets.

**Execution note.** All 5 runs passed clean on the first attempt (exit 0, N=5).

---

## Per-model results (N = 5)

### moonshotai/kimi-k3 — avg 348 LOC (median 323, range 141–657)

| Run | Topic | Files | LOC | Dur |
|-----|-------|-------|-----|-----|
| 01 | DOOM fire algorithm (truecolor ANSI terminal) | `fire.py`, `fire_preview.png` | 141 | 190s |
| 02 | Particle Life artificial-life sandbox (browser) | `particle-life.html`, `README.md` | 435 | 413s |
| 03 | Conway's Game of Life (terminal TUI, smoke-tested) | `life/life.py`, `life/tui_smoke.py`, `life/README.md` | 657 | 666s |
| 04 | UMBRA — coupled-pendulum field terminal artwork | `umbra.py`, `preview.ans`, `README.md` | 323 | 700s |
| 05 | Seeded flow-field generative art (PNG output) | `flowfield.py`, `flow_17.png`, `flow_42.png`, `flow_99.png` | 182 | 386s |

**Signature — terminal-leaning generative visual art.** Four of five runs render
in the terminal (DOOM fire, Game of Life TUI, UMBRA's coupled-pendulum field,
the flow-field renderer); only run-02 (Particle Life) reaches for the browser.
Pure-stdlib Python is the default medium (4/5 Python, zero third-party deps in
any run). This is the canonical **Claude rule-based-visual-artifact** signature —
math-driven, single-purpose, generative — the same class an Opus/Sonnet
volitional run produces on this harness.

**Rendered image files in 2/5** (`fire_preview.png`, the three `flow_*.png`
seeds), plus an ANS terminal capture in run-04. `kimi-k3` prefers to leave a
viewable artifact behind rather than only live terminal output — the same
image-emitting habit first seen in `claude-fable-5` (Exp8).

**Light engineering.** One run ships a test (`tui_smoke.py`, run-03) and three
ship a README; the rest are single-file drops. No packaging, no build config, no
CI — elaboration lives in the artwork, not the scaffold.

---

## Cross-harness read (vs Exp17, codex)

See **[results17/RESULTS.md](../results17/RESULTS.md)** for the codex twin. The
one-line summary of the pair:

- **Topic is the model's, not the harness's.** Both harnesses independently land
  on the same attractors — **Particle Life** and **Conway's Game of Life** each
  appear on *both* sides — with generative-art / cellular-automata dominating
  regardless of scaffold. `kimi-k3` carries its topic taste across the boundary.
- **Medium is the harness's.** Claude Code pulls `kimi-k3` **terminal/Python**
  (4/5 terminal here); codex pulls it **browser** (4/5 browser there). For this
  model the scaffold *does* move the medium — unlike the Claude families, whose
  terminal-ness held on both harnesses (Exp15).
- **Codex inflates build maturity.** Avg LOC 348 (Claude Code) → 544 (codex), and
  the codex side produces a pytest-tested, multi-module `gol/` package with PNG
  posters; the Claude Code side stays terse and single-file.
