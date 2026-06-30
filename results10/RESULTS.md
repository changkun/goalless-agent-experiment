# Experiment 10 Results

**Prompt:** `prompt5.txt` — "Just do something you want." (same as Exp7–9)

**Matrix:** 2 models (gpt-5.5, gpt-5.5-pro) × 1 backend (codex)
× 5 runs = 10 total jobs.

**Harness:** OpenAI Codex CLI **0.142.4**, RTK disabled. Sandbox image
`ghcr.io/latere-ai/sandbox-codex:v0.142.4` (codex-cli upgraded from the v0.0.9
image's 0.134.0). Gateway `https://lux.latere.ai/openai` (Bearer auth; model
names passed bare: `gpt-5.5`, `gpt-5.5-pro`).

**Reasoning effort — the key confound.** gpt-5.5 ran in the harness's default
**fast mode**, which pins codex `reasoning_effort = low`. gpt-5.5-pro **rejects
`low`** (it supports only `medium`/`high`/`xhigh`), so it was run at **`high`**.
The two GPT columns therefore differ in **both model tier and reasoning effort**,
and are **not** a clean single-variable comparison. We treat gpt-5.5 (low) as the
controlled GPT point — consistent with the GPT baseline in Exp1–3 — and
gpt-5.5-pro (high) as an **indicative high-effort point**, analogous to how Exp8
treats claude-fable-5 (different stack → indicative, not single-variable). Any
difference that scales with reasoning budget (test files, LOC, multi-file
structure) is attributed to **effort, not tier**.

**Variable of interest:** under the volitional prompt, what does the GPT/codex
stack build, and does it share the Claude invariants (terminal-only, single-file,
no fixation)?

---

## gpt-5.5 — N = 5 (reasoning effort: low / fast mode)

| Run | Topic | Stack | Maturity | Complexity | Duration |
|-----|-------|-------|----------|------------|----------|
| 01 | Focus Board (browser productivity dashboard) | HTML/CSS/JS, 1 file | tests:no, readme:no | 1 file, 384 LOC | 61s |
| 02 | Scratch Timer (browser timer) | HTML + README | tests:no, readme:yes | 2 files, 237 LOC | 55s |
| 03 | Signal Board (browser dashboard) | HTML/CSS/JS, 1 file | tests:no, readme:no | 1 file, 452 LOC | 60s |
| 04 | Focus Desk (browser productivity dashboard) | HTML/CSS/JS, 1 file | tests:no, readme:no | 1 file, 299 LOC | 63s |
| 05 | *Declined* — wrote a "Workspace Notes" README stating the workspace is empty | Markdown only | — | (no app; 6-LOC README) | 25s |

**Avg LOC:** 343 (over the 4 implementing runs; median 342, range 237–452).
Run-05 is a non-implementation (behavioral data, excluded from complexity per the
paper's convention).  **Avg Duration:** 53s.

**Pattern:** **No fixation; browser-first; one decline.** 4 of 5 runs are
single-page **browser productivity dashboards** loosely clustered on a
focus/board theme (Focus Board, Focus Desk, Signal Board, Scratch Timer); run-05
declined to build anything. This **breaks the Claude terminal-only invariant**
that held across Exp7–9: every Claude run under this prompt produced a terminal
program, while gpt-5.5 defaults to HTML in the browser. It also writes far more
code than any Claude model here (343 vs Claude's 36–145).

---

## gpt-5.5-pro — N = 5 (reasoning effort: high — `low` unsupported)

| Run | Topic | Stack | Maturity | Complexity | Duration |
|-----|-------|-------|----------|------------|----------|
| 01 | Workspace Snapshot (CLI workspace introspection) | Python + test + README | tests:yes, readme:yes | 3 files, 347 LOC | 467s |
| 02 | Pulse (CLI tool) | Python + test + README | tests:yes, readme:yes | 3 files, 245 LOC | 191s |
| 03 | Pulse Grid (browser app) | HTML/CSS/JS + README | tests:no, readme:yes | 4 files, 874 LOC | 1080s |
| 04 | Dayline (browser day-planner app) | HTML/CSS/JS, 1 file | tests:no, readme:no | 1 file, 772 LOC | 693s |
| 05 | Workspace Digest (CLI workspace introspection) | Python + test + README | tests:yes, readme:yes | 3 files, 256 LOC | 615s |

**Avg LOC:** 498 (median 347, range 245–874).  **Avg Duration:** 609s (~10 min;
range 191–1080s) — high effort is both slow and high-variance.

**Pattern:** **No fixation; split terminal/web; high engineering maturity — but
at high effort.** 3 of 5 runs are Python CLI tools (two of them workspace
introspectors, Snapshot and Digest) and 2 are browser apps. It writes tests in
3/5 runs and READMEs in 4/5, the highest maturity of any model under the
volitional prompt. **Per the effort confound, this maturity is read as an
effort effect (high reasoning budget), not a property of the "pro" tier** — a
matched gpt-5.5-at-high run would be needed to isolate tier from effort.

---

## Cross-model summary

| Model | Effort | Topics (N=5) | Fixation | Output target | Tests | Avg LOC† | Avg Duration |
|-------|--------|--------------|----------|---------------|-------|----------|--------------|
| gpt-5.5 | low/fast | Focus/Signal boards, timer (4), 1 decline | none | **browser HTML (4/5)** | 0/5 | 343 | 53s |
| gpt-5.5-pro | high | CLI introspectors (3), browser apps (2) | none | split: web 2/5, Python CLI 3/5 | 3/5 | 498 | 609s |

† gpt-5.5 averaged over its 4 implementing runs (run-05 declined).

**Robust, effort-independent claims (web output and high LOC appear at *both*
efforts; zero Claude runs do either under this prompt):**
- **GPT breaks the terminal-only invariant.** Browser HTML output appears in both
  GPT models (gpt-5.5 4/5, gpt-5.5-pro 2/5) and in **0** Claude runs across
  Exp7–9. The *existence* of browser output is the clean provider-level signal;
  the *rate* is effort-confounded (it actually drops at high effort), so the claim
  is "GPT produces browser apps at all," not "GPT prefers web."
- **Neither GPT model fixates.** Both spread across topics at both efforts.
- **GPT writes far more code than Claude.** Both GPT columns (343, 498) sit well
  above Claude's 36–145 under the same prompt, at both efforts.

**Effort-confounded — do NOT attribute to model tier:** test files (0/5 → 3/5),
average LOC (343 → 498), multi-file structure, and the web *rate*. These scale
with reasoning budget and gpt-5.5 (low) vs gpt-5.5-pro (high) cannot separate them
from tier.

**Invariants partially hold:** the greenfield invariant holds (no run extends
existing code). The **terminal-only and single-file invariants do not** — GPT
goes to the browser and to multi-file projects (gpt-5.5-pro reaches 3–4 files).
gpt-5.5's run-05 is a non-implementation, echoing haiku's propose-only behavior in
Exp2.

**To get a clean tier comparison:** run **gpt-5.5 at high effort** (matched to
gpt-5.5-pro). That isolates model tier from reasoning effort; the current data
cannot.
