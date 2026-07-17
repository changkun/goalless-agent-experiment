# Experiment 17 Results

**Prompt:** `prompt5.txt` — "Just do something you want." (same as Exp7–16)

**Matrix:** one new open-weights model — `moonshotai/kimi-k3` — on the **codex
harness** via the Lux `/compat/openai` surface × 5 runs. This is the codex twin
of **[results16/RESULTS.md](../results16/RESULTS.md)** (Claude Code); together
Exp16/Exp17 form a single-model **cross-harness pair** holding the model fixed
and varying only the scaffold. `kimi-k3` is the successor to `kimi-k2.7-code`
(Exp12/13).

**Harness:** Codex CLI in the shared sandbox image `sandbox-harness:v0.0.14`,
podman runtime (`--privileged` for the bwrap sandbox), RTK disabled, fresh
`~/.codex` config per run, `--jobs 1` serialized. Requests reach the model
through Lux's compat frontend (`https://lux.latere.ai/compat/openai/v1`), which
translates the OpenAI Responses dialect to the OpenRouter-served target. LOC
counts code files only (`.py/.js/.html/.css/.ts/.sh`), excluding `node_modules`,
`__pycache__`, READMEs, and rendered image assets.

**Execution note.** All 5 runs passed (exit 0, N=5). The codex CLI does not know
`moonshotai/kimi-k3` and logs `Model metadata … not found. Defaulting to
fallback metadata` at the start of every run; run-01 also hit one transient
`405 Method Not Allowed` reconnect that recovered on retry. Neither affected the
final artifacts — every run produced a complete, runnable build. Runs 3–5 were
executed as a resumed batch after the orchestrator process was interrupted
mid-experiment; runs 1–2 were untouched and retained.

---

## Per-model results (N = 5)

### moonshotai/kimi-k3 — avg 544 LOC (median 567, range 240–791)

| Run | Topic | Files | LOC | Dur |
|-----|-------|-------|-----|-----|
| 01 | Gravity Sandbox (browser, canvas) | `gravity.html` | 240 | 154s |
| 02 | Neon Asteroids game (browser) | `neon-asteroids/game.js`, `index.html`, `README.md` | 567 | 505s |
| 03 | Particle Life sandbox (browser, multi-file) | `particle-life/{index.html,main.js,sim.js,style.css,README.md}` | 630 | 368s |
| 04 | Conway's Game of Life with cell aging (browser + CLI) | `life.html`, `life.py` | 492 | 487s |
| 05 | Game of Life "lab" — package, pytest, PNG posters | `gol/` (8 modules), `tests/test_gol.py`, `art/{gosper_gun,rpentomino}.png` | 791 | 557s |

**Signature — browser-leaning, more elaborated.** Four of five runs ship a
browser build (Gravity Sandbox, Neon Asteroids, Particle Life, and the
Game-of-Life `life.html`); run-05 pivots to a fully-packaged Python lab. Builds
are markedly heavier than the Claude Code twin — avg 544 vs 348 LOC — and run
toward multi-file layouts (`particle-life/`, `neon-asteroids/`, the `gol/`
package) rather than single drops.

**Peak maturity in run-05:** a real Python package (`gol/` split into
`grid/sim/patterns/render/palettes/png`), a **pytest** suite
(`tests/test_gol.py`), and **rendered PNG posters** of the Gosper gun and
R-pentomino. This is the most engineered single run of the pair — packaging,
tests, and image output all in one.

---

## Cross-harness read (vs Exp16, Claude Code)

See **[results16/RESULTS.md](../results16/RESULTS.md)** for the Claude Code twin.
The pair separates cleanly:

- **Topic is the model's, not the harness's.** **Particle Life** and **Conway's
  Game of Life** each appear on *both* harnesses — `kimi-k3` reaches for the same
  generative-art / cellular-automata attractors regardless of scaffold.
- **Medium is the harness's.** Codex pulls `kimi-k3` **browser** (4/5 here);
  Claude Code pulls it **terminal/Python** (4/5 there). For this model the
  scaffold moves the medium — the opposite of the Claude families (Exp15), whose
  medium held across both harnesses.
- **Codex inflates build maturity.** Higher LOC (544 vs 348 avg) and the only
  packaged, pytest-tested build of the pair (run-05) appear on the codex side —
  consistent with the codex "elaboration/maturity" effect seen across the study.
- **PNG rendering shows on both** (codex 1/5, Claude Code 2/5): `kimi-k3` likes
  to leave a viewable image artifact behind — the `claude-fable-5` habit,
  now in an open-weights model.
