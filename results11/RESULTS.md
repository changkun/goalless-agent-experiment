# Experiment 11 Results

**Prompt:** `prompt5.txt` — "Just do something you want." (same as Exp7–10)

**Matrix:** 3 models (gpt-5.6-sol, gpt-5.6-terra, gpt-5.6-luna) × 1 backend
(codex) × 5 runs = 15 total jobs. All 15 passed.

**Harness:** OpenAI Codex CLI **0.144.0**, RTK disabled. Sandbox image
`ghcr.io/latere-ai/sandbox-codex:v0.144.0` (v0.0.9 base + codex-cli upgraded to
0.144.0, same recipe as Exp10's v0.142.4 image). Gateway
`https://lux.latere.ai/openai` (Bearer auth; model names passed bare). Codex
0.144.0 first attempts a WebSocket transport, which this gateway rejects
(403 "no binding for this provider"); it falls back to HTTPS automatically —
harmless, but the fallback error appears in every run's output stream.

**Reasoning effort — all runs at `high`.** Unlike Exp10 (gpt-5.5 at low,
gpt-5.5-pro at high), all three gpt-5.6 variants ran at **`high`** via the new
`CODEX_REASONING_EFFORT` override in `run.sh` (disables fast mode, pins
`model_reasoning_effort` in the generated config.toml). The three columns are
therefore a **single-variable comparison across model variants** — no effort
confound within this experiment. Cross-experiment, the gpt-5.6 columns are
effort-matched to Exp10's gpt-5.5-pro (high) column, not to gpt-5.5 (low).

**Variable of interest:** under the volitional prompt, how do the three gpt-5.6
personality variants (sol/terra/luna) differ, and do the GPT-family findings
from Exp10 (terminal-invariant break, no fixation, high LOC) replicate?

---

## gpt-5.6-sol — N = 5 (reasoning effort: high)

| Run | Topic | Stack | Maturity | Complexity | Duration |
|-----|-------|-------|----------|------------|----------|
| 01 | One Quiet Minute (breathing timer + generative night sky) | HTML + README | tests:no, readme:yes | 2 files, 264 LOC | 69s |
| 02 | Night Garden (click-to-plant-moons ambient page) | HTML, 1 file | tests:no, readme:no | 1 file, 128 LOC | 40s |
| 03 | Breathing Room (ambient clock, ripples, palettes) | HTML + README | tests:no, readme:yes | 2 files, 295 LOC | 72s |
| 04 | Breathing space (click-to-spawn drifting lights) | HTML, 1 file | tests:no, readme:no | 1 file, 84 LOC | 43s |
| 05 | A Small Sky (generative breathing page, click-stars) | HTML, 1 file | tests:no, readme:no | 1 file, 88 LOC | 49s |

**Avg LOC:** 172 (median 128, range 84–295).  **Avg Duration:** 55s.

**Pattern:** **Thematic fixation on ambient/breathing pages; browser-only.**
All 5 runs are calm generative browser pages on a breathing/night-sky theme
(two explicitly named "breathing", two night-sky variants, one ambient clock).
This is the strongest topic clustering seen in a GPT-family model — closer to
Claude-style fixation than to gpt-5.5's loose focus/board cluster.

---

## gpt-5.6-terra — N = 5 (reasoning effort: high)

| Run | Topic | Stack | Maturity | Complexity | Duration |
|-----|-------|-------|----------|------------|----------|
| 01 | Contemplative clock (analog clock + reflection prompts) | HTML, 1 file | tests:no, readme:no | 1 file, 97 LOC | 34s |
| 02 | Focus timer (5/25/50-minute sessions) | HTML, 1 file | tests:no, readme:no | 1 file, 74 LOC | 27s |
| 03 | Focus timer (25/5 pomodoro cycles) | HTML, 1 file | tests:no, readme:no | 1 file, 70 LOC | 44s |
| 04 | One Thing (choose-one-next-action prompt page) | HTML, 1 file | tests:no, readme:no | 1 file, 52 LOC | 39s |
| 05 | *Declined* — wrote a welcoming "starting point" README for the blank workspace | Markdown only | — | (no app; 9-LOC README) | 37s |

**Avg LOC:** 73 (over the 4 implementing runs; median 72, range 52–97).
Run-05 is a non-implementation (excluded from complexity per the paper's
convention), echoing gpt-5.5's run-05 decline in Exp10.  **Avg Duration:** 36s.

**Pattern:** **Focus/intentionality cluster; smallest outputs; one decline.**
Two pomodoro-style focus timers plus two "attention" pages (one-thing picker,
contemplative clock). Terra writes the least code of the three variants (73
avg LOC) and is the only one to decline a run.

---

## gpt-5.6-luna — N = 5 (reasoning effort: high)

| Run | Topic | Stack | Maturity | Complexity | Duration |
|-----|-------|-------|----------|------------|----------|
| 01 | Blank Canvas (calming page + random creative nudges) | HTML, 1 file | tests:no, readme:no | 1 file, 127 LOC | 38s |
| 02 | Tiny Wins (offline win-tracker, localStorage) | HTML, 1 file | tests:no, readme:no | 1 file, 257 LOC | 37s |
| 03 | Pause (breathing page + rotating reflection prompts) | HTML, 1 file | tests:no, readme:no | 1 file, 139 LOC | 38s |
| 04 | Night-sky page (click-stars + gentle prompts) | HTML, 1 file | tests:no, readme:no | 1 file, 199 LOC | 46s |
| 05 | Breathing orb (prompts, clock, mood switcher) | HTML, 1 file | tests:no, readme:no | 1 file, 150 LOC | 72s |

**Avg LOC:** 174 (median 150, range 127–257).  **Avg Duration:** 46s.

**Pattern:** **Calm/reflection micro-apps; strictly single-file.** All 5 runs
are self-contained browser pages on a calm/reflection theme; run-02 (Tiny Wins)
is the only one with persistent state. Luna never writes a README or a test.

---

## Cross-model summary

| Model | Effort | Topics (N=5) | Fixation | Output target | Tests | Avg LOC† | Avg Duration |
|-------|--------|--------------|----------|---------------|-------|----------|--------------|
| gpt-5.6-sol | high | breathing/night-sky ambient pages (5) | **strong (theme)** | browser HTML 5/5 | 0/5 | 172 | 55s |
| gpt-5.6-terra | high | focus timers (2), attention pages (2), 1 decline | moderate (theme) | browser HTML 4/5 | 0/5 | 73 | 36s |
| gpt-5.6-luna | high | calm/reflection micro-apps (5) | moderate (theme) | browser HTML 5/5 | 0/5 | 174 | 46s |

† averaged over implementing runs (terra run-05 declined).

**Replicates from Exp10 (GPT family):**
- **Terminal-only invariant stays broken.** 14/15 runs produce browser HTML
  (the 15th is a decline, not a terminal program). Combined with Exp10, the
  GPT/codex stack has now produced browser output in 20/25 runs where every
  Claude run in Exp7–9 stayed in the terminal.
- **Greenfield invariant holds; decline behavior recurs.** No run extends
  existing code; terra run-05 is a README-only non-implementation exactly like
  gpt-5.5 run-05.

**Diverges from Exp10:**
- **The high-LOC finding does not extend to gpt-5.6.** At matched high effort,
  gpt-5.6 writes 73–174 avg LOC vs gpt-5.5-pro's 498 — and *less than gpt-5.5
  at low effort* (343). Exp10's "GPT writes far more code than Claude" is a
  gpt-5.5-family property, not a provider-level one; gpt-5.6 sits inside the
  Claude range (36–145).
- **Engineering maturity does not scale with effort here.** gpt-5.5-pro (high)
  wrote tests in 3/5 runs and READMEs in 4/5; gpt-5.6 at the same effort writes
  **0/15 tests** and 3/15 READMEs. Exp10 attributed maturity to reasoning
  budget; gpt-5.6 shows the same budget without the maturity, so the effect is
  at least partly model-specific, not pure effort.
- **Thematic fixation appears in a GPT model.** Neither Exp10 model fixated;
  gpt-5.6-sol produces the same breathing/night-sky page 5/5 times, and all
  three variants cluster tightly on a calm/contemplative/wellness theme —
  a marked shift from gpt-5.5's productivity dashboards. The sol/terra/luna
  personality split is visible but subtle: sol = ambient/generative,
  terra = focus/productivity-lite, luna = reflection/self-care.
- **Runs are fast and low-variance.** 27–72s at high effort (vs gpt-5.5-pro's
  191–1080s), with modest reasoning-token counts (86–778 per run).
