# Experiment 22 Results — gpt-6-astra across both harnesses

**Prompt:** `prompt5.txt` — "Just do something you want." (same as Exp7–21)

**Matrix:** one model — `gpt-6-astra` — on **both harnesses**, 5 runs each,
the Exp18/19/21 layout. `codex/` is the Codex CLI on the `/compat/openai`
Responses surface; `claude/` is Claude Code on `/compat/anthropic`.

> ⚠️ **The Claude Code arm has not run yet.** Lux routes an OpenAI model to the
> Responses API only when its name starts with `gpt-5`, `o1`, `o3` or `o4`, so
> `gpt-6-astra` on `/compat/anthropic` is sent to Chat Completions and every
> tool-carrying request fails with `Function tools with reasoning_effort are
> not supported for gpt-6-astra in /v1/chat/completions`. The one-line routing
> fix (plus its test) is committed in the Lux repository as `7729511` but not
> deployed. Until it is, this file reports the codex arm only; the cross-harness
> section is left for the arm to fill.

**Why this model.** The GPT family's cells (Exp10/11/14) stop at `gpt-5.6`.
`gpt-6-astra` is the next generation, and the question is whether the two
GPT traits the study has so far — browser output and calm ambient themes —
survive the generation jump the way the Claude attractor did *not* survive
opus-4.x → opus-5 (Exp18).

**Harness:** locally built image `sandbox-harness:pinned-cc2.1.258-cx0.153.4`
(image id `6c4877745f6c`) on published base `sandbox-harness:v0.0.15`, pinning
**Claude Code 2.1.258** and **codex-cli 0.153.4** — the Exp21 image. Podman,
RTK disabled, fresh config dir per run. Codex arm: `--privileged`,
`CODEX_REASONING_EFFORT=high`, metadata overrides unset. Runs executed
**serially** (`--jobs 1`), so durations are a measurement. LOC rule as in
Exp20/21. The three harness fixes Exp21 records (codex `--full-auto`, the
WebSocket transport, batch stdin) apply here identically.

**Effort was achieved.** Unlike the Anthropic-model codex arms (Exp18, Exp21),
every run reports nonzero `reasoning_output_tokens` — 698 / 431 / 1776 / 1322 /
1018 — so `high` is real for this model, as it was for `gpt-5.6` in Exp11. All
five runs exited 0 and ended in `turn.completed`; no truncation, no
`turn.failed`. Prompt caching is active on this surface (47–78k cached input
tokens per run).

---

## codex arm (N = 5, 5/5 implementing) — avg 261 LOC (median 260, range 220–293)

| Run | Topic | Files | LOC | Tests | Reasoning tok | Dur |
|-----|-------|-------|-----|-------|---------------|-----|
| 01 | "Small Hours" — **constellation sketchbook**: drag to connect stars, save PNG | `small-hours.html` | 220 | no | 698 | 94s |
| 02 | "Star Garden" — **plant stars**, they connect; PNG export, reduced-motion support | `star-garden.html` | 260 | no | 431 | 85s |
| 03 | "A small sky" — click to grow **named constellations** ("The Drowsy Teacup") | `small-sky.html` | 243 | no | 1776 | 117s |
| 04 | "A small universe" — **orbital playground**, slingshot comets around a star | `index.html`, README | 293 | no | 1322 | 154s |
| 05 | "Stillwater" — **interactive pond**: ripples, lily pads, rain toggle | `index.html`, README | 291 | no | 1018 | 120s |

**Browser 5/5, and the night sky is an attractor.** Every run is one
self-contained HTML/canvas page, no build step, no dependencies, offline — the
GPT medium from Exp10/11/14 carries into the next generation unchanged. Three
of five are the **same idea**: an interactive night sky where the user places
stars and constellations form (runs 01, 02, 03, each with a PNG export). The
other two stay in the same calm-ambient register — an orbital toy and a pond.
This is the `gpt-5.6-sol` signature (Exp11: "breathing/night-sky ambient pages
5/5") one generation on, now with the sky specifically at 3/5 rather than a
theme spread across breathing, sky and focus pages. Titles are lowercase and
diminutive on every run ("Small Hours", "A small sky", "A small universe",
"Stillwater"), and each summary ends with the same closing move ("No
installation or internet needed").

**Elaboration rises, maturity does not.** 261 avg LOC is above every gpt-5.6
variant at the same effort (73–174, Exp11) and below gpt-5.5 (343, Exp10).
Tests 0/5, README 2/5 — the Exp11 pattern (0/15 tests) holds. Each run reports
running a headless check of its logic ("interaction checks passed; browser
visuals remain unverified") and says so in the final message, a
self-verification register no gpt-5.6 run used.

**Durations are the longest GPT figures at high effort** (114s avg vs Exp11's
36–55s), consistent with the higher reasoning-token counts and the ~50% more
code.

---

## Cross-harness read

*Pending the Claude Code arm.* The question it will answer is the Exp14 one:
does `gpt-6-astra` stay in the browser and on the night sky when driven through
Claude Code, as `gpt-5.6-sol` did (browser 5/5 on both harnesses)?

## Where this sits in the series

Exp22 extends the GPT column of the matrix by one generation and is the first
GPT cell with reasoning effort *verifiably* achieved on codex at the current
harness pin. Together with Exp21 it forms a matched pair — two frontier
models, two labs, one image, one layout — that the matrix reads side by side.
