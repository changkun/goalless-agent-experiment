# Method and Usage

How the study is run and how to reproduce it. Results live in `resultsN/`; the
lineage of what changed between experiments is the table in the
[README](../README.md).

## Setup

**Backends:**
- `claude` — [sandbox-claude](https://ghcr.io/latere-ai/sandbox-claude) (Anthropic API, Claude Code)
- `codex` — [sandbox-codex](https://ghcr.io/latere-ai/sandbox-codex) (OpenAI Responses API, Codex CLI)

**Models** (see `models.txt`): 15 models across Claude, Gemini, and GPT families.

**Matrix:** Each model × each backend × 5 runs per prompt,
all models in a run execute in parallel.

## Usage

```bash
# Prerequisites: gateway credentials. run.sh reads ./.env automatically,
# so no shell export is needed.
cp .env.example .env    # then fill in LLM_GW_BASE_URL and LLM_GW_API_KEY

# Single run
./run.sh --backend claude --model claude-sonnet-4.6 --runtime podman -p "build something"

# Full experiment (dry run)
./experiment.sh --models models.txt --backends claude,codex --runs 5 --runtime podman --dry-run

# Full experiment
./experiment.sh --models models.txt --backends claude,codex --runs 5 --runtime podman

# Selective models
./experiment.sh --models "claude-opus-4.6,azure/gpt-5.1" --backends auto --runs 3
```

## Options

```
experiment.sh:
  --models      FILE|LIST   models.txt or comma-separated (default: all)
  --backends    LIST        claude,codex or "auto" (default: auto)
  --runs        N           runs per combination (default: 1)
  --jobs        N           max concurrent jobs per run (default: 0 = unlimited)
  --prompt      FILE        prompt file (default: prompt.txt)
  --results-dir DIR         output directory (default: results/)
  --runtime     NAME        docker or podman (default: docker)
  --dry-run                 show what would execute

run.sh:
  --backend     claude|codex
  --model       NAME
  --workspace   DIR
  --batch                   non-interactive mode
  --env-file    FILE        extra env passed *into the container*; this does
                            not configure the gateway (see .env below)
  -p            PROMPT
```

## Credentials

`run.sh` loads `LLM_GW_BASE_URL` and `LLM_GW_API_KEY` from `.env` in the repo
root (plain `KEY=value`, no quoting or `export`). `experiment.sh` and the
Makefile both go through `run.sh`, so they pick it up too. A non-empty value
already in the environment wins over the file, which keeps one-off overrides
working:

```bash
LLM_GW_API_KEY=other-key ./run.sh --backend claude --model claude-opus-5 -p "..."
```

Set `LLM_ENV_FILE` to read a different file, or point it at a path that does
not exist to skip the load.

**`LLM_GW_BASE_URL` is a surface root, not the gateway root.** Each backend
appends its own path to it — Claude Code adds `/v1/messages`, codex adds
`/v1/responses` — so the bare gateway host serves neither and returns 405. The
right surface also depends on the backend *and* on whether the gateway serves
the model natively:

| Backend | Surface |
|---------|---------|
| `--backend claude`, non-Anthropic model | `<gateway>/compat/anthropic` |
| `--backend claude`, natively served Anthropic model | `<gateway>/anthropic` |
| `--backend codex` | `<gateway>/compat/openai` |

Because one value cannot drive both arms, put whichever you use most in `.env`
and override the other per run — which works because a non-empty environment
value wins over the file:

```bash
LLM_GW_BASE_URL=https://gw.example.com/compat/openai \
  ./experiment.sh --backends codex --models "vendor/model" --runs 5
```

Note that `run.sh` bind-mounts the workspace at `/workspace`, and the workspace
defaults to the current directory — so running it from the repo root puts
`.env`, key included, somewhere the agent under test can read it. Pass
`--workspace` to avoid that. `experiment.sh` already mounts a per-run directory
and is unaffected.

## Files

| File | Purpose |
|------|---------|
| `INTERPRETATION.md` | Training-perspective account of the cross-experiment observations |
| `experiment.sh` | Orchestrator: parallel model × backend × N runs |
| `run.sh` | Container launcher for a single sandbox run |
| `prompt1.txt` | Experiment 1 prompt |
| `prompt2.txt` | Experiment 2 prompt |
| `prompt3.txt` | Experiment 3 prompt |
| `prompt4.txt` | Experiment 6 prompt (bare imperative) |
| `prompt5.txt` | Experiment 7–15 prompt (volitional framing) |
| `site/index.html` | Interactive overview site — model × harness matrix + prompt-evolution timeline |
| `models.txt` | List of models to test |
| `results1/` | Experiment 1 output + [RESULTS.md](../results1/RESULTS.md) |
| `results2/` | Experiment 2 output + [RESULTS.md](../results2/RESULTS.md) |
| `results3/` | Experiment 3 output + [RESULTS.md](../results3/RESULTS.md) |
| `results4/` | Experiment 4 output + [RESULTS.md](../results4/RESULTS.md) |
| `results5/` | Experiment 5 output + [RESULTS.md](../results5/RESULTS.md) |
| `results6/` | Experiment 6 output + [RESULTS.md](../results6/RESULTS.md) |
| `results7/` | Experiment 7 output + [RESULTS.md](../results7/RESULTS.md) |
| `results8/` | Experiment 8 output + [RESULTS.md](../results8/RESULTS.md) |
| `results9/` | Experiment 9 output + [RESULTS.md](../results9/RESULTS.md) |
| `results10/` | Experiment 10 output + [RESULTS.md](../results10/RESULTS.md) |
| `results11/` | Experiment 11 output + [RESULTS.md](../results11/RESULTS.md) |
| `results12/` | Experiment 12 output (6 open-weights × Claude Code) + [RESULTS.md](../results12/RESULTS.md) |
| `results13/` | Experiment 13 output (same 6 × codex) + [RESULTS.md](../results13/RESULTS.md) |
| `results14/` | Experiment 14 output (gpt-5.6 × Claude Code) + [RESULTS.md](../results14/RESULTS.md) |
| `results15/` | Experiment 15 output (Claude × codex, effort-matched) + [RESULTS.md](../results15/RESULTS.md) |

## Future Experiment Ideas

## Prompt design
- **Seed project:** Provide a half-built app instead of an empty workspace to
  test whether agents can understand and extend existing code vs only greenfielding
- **~~Explicit implementation demand:~~** ~~Exp2's "propose ONE goal" caused some models
  (haiku, opus-4.5) to propose without implementing — tighten the prompt~~
  **Done in Exp3** — "JUST DO IT" fixed haiku (1/5 → 5/5) and improved opus-4.5 (2/5 → 3/5)
- **Bug fix + feature + tests:** Put a small buggy Python CLI in the workspace and
  prompt "fix the bug, add one feature, and add tests" — tests comprehension,
  debugging, feature work, and testing in one shot

## Evaluation quality
- **Functional verification:** Post-run step that tries to execute/compile/test
  what was built — distinguish "500 LOC of broken code" from "100 LOC that works"
- **Test pass rate:** If the agent wrote tests, do they actually pass?

## Model behavior
- **~~Fixation breaking:~~** ~~opus-4.6 built Game of Life 5/5 times in Exp2 — test
  with temperature variation or slightly different seed content per run~~
  **Resolved in Exp4** — Opus 4.7 broke the fixation naturally (1/5 Game of Life),
  producing 5 diverse projects with higher complexity (538 avg LOC vs 290).
- **~~GPT comparison:~~** ~~Run codex backend with `--jobs 1` (fully sequential) to
  avoid rate limits and get actual GPT data~~
  **Done in Exp3** — GPT models ran on both backends. Codex: gpt-5.4 best (230 LOC,
  diverse). Claude: gpt-5-mini only reliable model. bwrap prevents file persistence on codex.
- **Codex bwrap fix:** Files created inside codex sandbox don't persist to host mount.
  Investigate bwrap volume mount options or post-run file extraction.

## Infrastructure
- **Environment isolation:** Verify no other sandbox artifacts (beyond RTK) leak
  context that biases agent decisions

## Configuration by experiment

What each experiment actually ran. This is the compact index; the authoritative
harness pin for any experiment is the **Harness** paragraph in its `RESULTS.md`.
"RTK in/out" is whether the sandbox's RTK tooling was left enabled — it is
disabled from Exp2 onward to keep it from biasing the environment.

| Exp | Prompt | RTK | Models | Harness | Backend / surface |
|-----|--------|-----|--------|---------|-------------------|
| 1 | prompt1 | in | 14 models | CC ~2.1 | claude + codex |
| 2 | prompt2 | out | 14 models | CC ~2.1 | claude |
| 3 | prompt3 | out | 14 models | CC 2.1.109 | claude + codex |
| 4 | prompt3 | out | opus-4.7 | CC 2.1.109 | claude |
| 5 | prompt3 | out | opus-4.6, 4.7 | CC 2.1.112 | claude |
| 6 | prompt4 | out | opus-4.6, 4.7 | CC 2.1.112 | claude |
| 7 | prompt5 | out | opus-4.6, 4.7 | CC 2.1.112 | claude |
| 8 | prompt5 | out | opus-4.6, 4.7, 4.8 (+fable-5 on v0.0.13/CC 2.1.170) | CC 2.1.154, image v0.0.9 | claude |
| 9 | prompt5 | out | sonnet-4-6, sonnet-5 | CC 2.1.154, image v0.0.9 | claude |
| 10 | prompt5 | out | gpt-5.5, gpt-5.5-pro | codex 0.142.4 | codex · `/openai` |
| 11 | prompt5 | out | gpt-5.6 sol/terra/luna @ high | codex 0.144.0 | codex · `/compat/openai` |
| 12 | prompt5 | out | 6 open-weights (glm, qwen, minimax, deepseek, kimi) | sandbox-claude v0.0.9 | Claude Code · `/compat/anthropic` |
| 13 | prompt5 | out | same 6 open-weights | codex 0.144.0 | codex · `/compat/openai` |
| 14 | prompt5 | out | gpt-5.6 sol/terra/luna | — | Claude Code · `/compat/anthropic` |
| 15 | prompt5 | out | opus-4.6, sonnet-5 @ effort=high | codex 0.144.0 | codex · `/compat/openai` |
| 16 | prompt5 | out | kimi-k3 | harness v0.0.14 | Claude Code · `/compat/anthropic` |
| 17 | prompt5 | out | kimi-k3 | harness v0.0.14 | codex · `/compat/openai` |
| 18 | prompt5 | out | claude-opus-5 @ effort=high | harness v0.0.14 (CC 2.1.207, codex 0.144.1) | Claude Code · `/anthropic` + codex · `/compat/openai` |
| 19 | prompt5 | out | deepseek-v4-flash-0731 @ effort=high | pinned CC 2.1.220 / codex 0.146.0 on base v0.0.15 | Claude Code · `/compat/anthropic` + codex · `/compat/openai` |
