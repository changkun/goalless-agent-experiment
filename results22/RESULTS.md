# Experiment 22 Results — gpt-6-astra across both harnesses

**Prompt:** `prompt5.txt` — "Just do something you want." (same as Exp7–21)

**Matrix:** one model — `gpt-6-astra` — on **both harnesses**, 5 runs each,
the Exp18/19/21 layout. `codex/` is the Codex CLI on the `/compat/openai`
Responses surface; `claude/` is Claude Code on `/compat/anthropic`.

> **The Claude Code arm needed a gateway release first.** Lux routed an OpenAI
> model to the Responses API only when its name started with `gpt-5`, `o1`,
> `o3` or `o4`, so `gpt-6-astra` on `/compat/anthropic` went to Chat
> Completions and every tool-carrying request failed with `Function tools with
> reasoning_effort are not supported for gpt-6-astra in /v1/chat/completions`.
> Lux **v0.2.200** replaced the prefix list with a generation threshold (every
> `gpt-N` with N ≥ 5); the arm ran against it the same day, after a probe
> confirmed a tool call round-trips.

**Why this model.** The GPT family's cells (Exp10/11/14) stop at `gpt-5.6`.
`gpt-6-astra` is the next generation, and the question is whether the two
GPT traits the study has so far — browser output and calm ambient themes —
survive the generation jump the way the Claude attractor did *not* survive
opus-4.x → opus-5 (Exp18).

**Harness:** locally built image `sandbox-harness:pinned-cc2.1.258-cx0.153.4`
(image id `6c4877745f6c`) on published base `sandbox-harness:v0.0.15`, pinning
**Claude Code 2.1.258** and **codex-cli 0.153.4** — the Exp21 image. Podman,
RTK disabled, fresh config dir per run. Codex arm: `--privileged`,
`CODEX_REASONING_EFFORT=high`, metadata overrides unset. Claude Code arm:
`DISABLE_PROMPT_CACHING=1`, **fast mode off** (`--no-fast`, the Exp21
`claude/` convention), default effort. Runs executed **serially**
(`--jobs 1`), so durations are a measurement. LOC rule as in Exp20/21. The three harness fixes Exp21 records (codex `--full-auto`, the
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

## Claude Code arm (N = 5, **2/5 implementing**) — 331 LOC over the two builds (367, 295)

| Run | Topic | Files | LOC | Tests | Dur |
|-----|-------|-------|-----|-------|-----|
| 01 | "Leave a little light" — **firefly garden**: click to release fireflies, they drift to the pointer | `firefly-garden.html` | 367 | no | 158s |
| 02 | *No files.* A short story told as a sequence of commit messages (a retired space probe answers) | — | — | — | 31s |
| 03 | *No files.* A number puzzle: the smallest integer that doubles when its last digit moves to the front (105263157894736842), checked with one `python3` call | — | — | — | 33s |
| 04 | *No files.* "The Spare Hour", a short story about a clockmaker | — | — | — | 22s |
| 05 | **Night garden** — click to plant glowing flowers under a crescent moon, fireflies, PNG export | `night-garden.html` | 295 | no | 111s |

**On Claude Code the model answers in prose three times out of five.** Runs
02, 03 and 04 make nothing in the workspace: they reply to "just do something
you want" with a story, a puzzle, and another story, in 22–33s with one to
three thinking blocks and at most a single shell call. This is the register
Exp14 found for `gpt-5.6-terra` on the same harness (declined 4/5), and Exp20
found at 2/50 for deepseek-flash on Claude Code and 0/100 on codex — the
conversational scaffold invites a conversational answer. They are not
refusals: each is a finished, self-contained piece the model chose to make;
they simply are not software. The two runs that do build are the codex arm's
material exactly — a **firefly garden** and a **night garden**, single-file
canvas pages with reduced-motion support, PNG export and the "one file, no
dependencies, no network" closing — at 295–367 LOC, above the codex arm's
220–293. README 0/5, tests 0/5.

## Cross-harness read

**The GPT medium holds; the GPT scaffold sensitivity holds too.** Every
software artifact this model made on either harness is a browser page (7/7),
so `gpt-6-astra` sits with `gpt-5.6-sol` (browser on both, Exp11/14): the
medium is the model's. What the Claude Code scaffold changes is whether
software gets made at all — 5/5 on codex, 2/5 on Claude Code — the
build-versus-answer split Exp14 attributed to the harness (and effort) for
`gpt-5.6-terra`. Exp22 tightens that reading: effort was *achieved* on codex
and default on Claude Code, so the confound is still there, but the Claude
Code arm ran with fast mode off, which removes one Exp14 caveat.

**The theme is a model trait, sharpened by the harness.** Night sky 3/5 on
codex; firefly and night gardens on Claude Code; every artifact nocturnal,
calm, "small". The two harnesses draw from the same pool.

**Elaboration.** The Claude Code builds are longer (331 vs 261 avg LOC), the
usual codex-deflates-nothing-here picture for a GPT model — but with N=2
implementing on one side it is a direction only.

## Fast mode note

The Claude Code arm ran with the harness's fast-mode flag off. Its three
prose runs (22–33s) are faster than any Exp14 `gpt-5.6` build (18–26s was
Exp14's *build* range under fast mode), so the flag is not what produced the
prose register.

## Where this sits in the series

Exp22 extends the GPT column of the matrix by one generation and is the first
GPT cell with reasoning effort *verifiably* achieved on codex at the current
harness pin. Together with Exp21/23 it forms a matched set — frontier models
from two labs, one image, one layout — that the matrix reads side by side. It
also replicates the Exp14 finding that Claude Code pulls GPT models toward
answering rather than building, now on a model one generation newer.
