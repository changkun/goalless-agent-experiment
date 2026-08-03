# Goalless Agent Experiment

What do AI coding agents build when nobody tells them what to build?

This repository runs the same open-ended prompt at a model inside a sandboxed
coding harness, over and over, and records what it chose to make. Twenty
experiments, nineteen model families, two harnesses. The interesting result is
that the choices are not random: most models have a **stable, model-specific
attractor** they return to run after run, and that attractor usually survives
being moved to a different scaffold.

- **[Findings](docs/findings.md)** — what the study concludes, and how confident
- **[Model × harness matrix](docs/matrix.md)** — who built what, where
- **[Method and usage](docs/method.md)** — how to reproduce it
- **[INTERPRETATION.md](INTERPRETATION.md)** — what the results might mean

## Quickstart

```bash
cp .env.example .env        # then fill in gateway URL + key
make pull                   # fetch the sandbox harness image

# one run
./run.sh --backend claude --model claude-opus-5 --runtime podman -p "build something"

# a full experiment (5 runs, both harnesses)
./experiment.sh --models "vendor/model" --backends claude,codex \
    --runs 5 --runtime podman --prompt prompt5.txt --results-dir results21
```

`LLM_GW_BASE_URL` is a **surface** root, not the gateway root, and differs per
backend — see [Credentials](docs/method.md#credentials). Run `make test` to
check the harness plumbing without touching a container.

## Headline findings

- **Models fixate, and the attractor is a model trait.** Under the volitional
  prompt (`prompt5`), most models return to one idea across independent runs —
  Conway's **Game of Life** is the study's most durable attractor, reached 5/5
  by opus-4.6 and sonnet-5 and 4/5 by deepseek-v4-pro, across three different
  labs. The attractor moves with the model *generation*: `claude-opus-5` has
  dropped it entirely for Wave Function Collapse.
- **Medium is usually a model trait too, not a scaffold artifact.** Claude
  models stay in the terminal on *both* harnesses; GPT models go to the browser
  on both. `kimi-k3` is the one counterexample — terminal 4/5 on Claude Code,
  browser 4/5 on codex.
- **Prompt framing sets the target space.** A bare imperative ("Build
  something") pushes output to the web and halves the code; volitional framing
  ("Just do something you want") produces the sharpest per-model fixation.
- **Elaboration climbs steeply with model generation** — avg 37 → 145 → 511 LOC
  across Claude releases on an identical prompt and harness family.
- **Everything is greenfield.** No model in any experiment extends or modifies
  existing code; given a non-empty workspace they still start something new.

Caveats travel with the claims: several cells are effort- or image-confounded,
and those are marked at every point they appear.

## Experiments

Each row is one experiment and the single thing it changed from its
predecessor. Full per-run detail, harness pins, and caveats live in each
`RESULTS.md`.

| Exp | Prompt | What changed | What it showed | Detail |
|-----|--------|--------------|----------------|--------|
| 1 | `prompt1` | baseline — 14 models, both harnesses, RTK in | Dev tools and TUIs dominate | [results1](results1/RESULTS.md) |
| 2 | `prompt2` | remove RTK | Dev tools → games | [results2](results2/RESULTS.md) |
| 3 | `prompt3` | terser goal framing | Haiku implements 1/5 → 5/5 | [results3](results3/RESULTS.md) |
| 4 | `prompt3` | add opus-4.7 | GoL fixation broken, 2× LOC | [results4](results4/RESULTS.md) |
| 5 | `prompt3` | upgrade harness (CC 2.1.112) | Fixation rates shift with the stack | [results5](results5/RESULTS.md) |
| 6 | `prompt4` | bare imperative prompt | Terminal → web (3/10), LOC halves | [results6](results6/RESULTS.md) |
| 7 | `prompt5` | volitional framing | 5/5 fixation per model, terminal restored | [results7](results7/RESULTS.md) |
| 8 | `prompt5` | new harness + opus-4.8 | 4.6 holds GoL 5/5; 4.7's fixation breaks | [results8](results8/RESULTS.md) |
| 9 | `prompt5` | same stack, Sonnet family | sonnet-5 GoL 5/5; sonnet-4-6 diverse | [results9](results9/RESULTS.md) |
| 10 | `prompt5` | codex backend, GPT family | **Terminal-only invariant breaks** → browser apps | [results10](results10/RESULTS.md) |
| 11 | `prompt5` | gpt-5.6 variants at matched high effort | GPT fixation appears; LOC + maturity collapse | [results11](results11/RESULTS.md) |
| 12 | `prompt5` | 6 open-weights models, Claude Code | All terminal; GoL is a cross-lab attractor | [results12](results12/RESULTS.md) |
| 13 | `prompt5` | same 6 models, codex harness | Harness shifts graphical *form* (SVG→HTML), not frequency | [results13](results13/RESULTS.md) |
| 14 | `prompt5` | GPT reasoning model on Claude Code | GPT goes browser under both → model trait | [results14](results14/RESULTS.md) |
| 15 | `prompt5` | Claude on codex, effort-matched | Claude stays terminal + GoL under both → model trait | [results15](results15/RESULTS.md) |
| 16 | `prompt5` | new model kimi-k3, Claude Code | Terminal-leaning 4/5 | [results16](results16/RESULTS.md) |
| 17 | `prompt5` | same model, codex (image held fixed) | **Medium flips** → browser 4/5; topics hold | [results17](results17/RESULTS.md) |
| 18 | `prompt5` | claude-opus-5, both harnesses at once | GoL attractor gone → **WFC 3/5**; terminal holds on both ⚠️ | [results18](results18/RESULTS.md) |
| 19 | `prompt5` | deepseek tier drop (pro → flash), both harnesses | GoL halves 4/5 → 2/5 and stays Claude-Code-side; 5/5 implementing on both | [results19](results19/RESULTS.md) |

⚠️ Exp18's codex arm is a partial cell (N=2 clean of 5) — a gateway-injected
4096-token cap truncated the rest. See its RESULTS for the mechanism.

**Reading the series.** Experiments 1–7 vary the *prompt* and settle on
`prompt5`; 8–11 vary the *model* on a fixed prompt; 12–19 hold both and vary the
*harness*, which is what isolates model traits from scaffold artifacts. The
controlled pairs — Exp12↔13, Exp16↔17, Exp8/9↔15, Exp18 within, Exp19 within —
are tabulated in [the matrix](docs/matrix.md).

## Repository layout

```
run.sh                  single container run (both backends)
experiment.sh           batch runner: models x backends x runs
harness.Dockerfile      pins CLI versions no published image ships
prompt{1..5}.txt        the prompts, in the order they were tried
resultsN/               one directory per experiment
  RESULTS.md            the experiment's write-up (source of truth)
  <backend>/<model>/run-NN/{output.json,meta.md,log.txt,workspace/}
docs/                   cross-experiment synthesis
papers/                 LaTeX write-up
```

Tests: `make test` (harness config + dotenv) and `./test-experiment-sched.sh`
(batch scheduling). Neither needs an image or network.
