# Interpretation: Why Training Predicts These Behaviors

This document offers a training-centric reading of the observations across
Exp1–11 (11 experiments, 22 models, multiple harness versions, five prompts).
It is **post-hoc interpretation of observational data**, not a controlled
study of training interventions: we observe deployed models whose training
pipelines are proprietary, so every mechanism below is a hypothesis ranked by
how much of the data it explains, with tests that could falsify it. Read
[README.md](README.md) for the observations themselves.

## 1. A minimal causal model

An agent's behavior in these experiments is the composition of four layers:

```
behavior = decoding( context | post-training( pretraining prior ) )

  pretraining prior   what code/artifacts are dense in the corpus
  post-training       SFT + RLHF/RLAIF + persona/character tuning + agentic RL
  context             system prompt (harness), tool set, workspace, user prompt
  decoding            sampling temperature, reasoning budget, stop conditions
```

Every prompt in this study progressively *removes* task specification, ending
with "Just do something you want." (prompt5), which removes it entirely. A
model trained as a conditional policy `π(action | task, context)` receives no
task term — so what we observe is the **shaped prior**: the modes that
pretraining installed and post-training sharpened, filtered through whatever
conditioning the harness still supplies. Each observation below falls out of
one or more of these layers.

## 2. Fixation is mode collapse, not preference

**Observation.** Under the volitional prompt, several models produce the
*same* artifact in 5/5 independent sessions: opus-4.6 → Game of Life (Exp7,
Exp8), opus-4.7 → Mandelbrot (Exp7), sonnet-5 → Game of Life (Exp9),
gpt-5.6-sol → breathing/night-sky pages (Exp11). Other models on the same
stack spread across 4–5 topics.

**Training account.** RLHF-style post-training optimizes a policy against a
reward model under a KL penalty to the base model. This is known to *sharpen*
the output distribution — the aligned model concentrates probability mass on
a narrow set of high-reward completions, trading diversity for expected
reward (documented as reduced output diversity in RLHF-tuned models, e.g.
Kirk et al. 2023, arXiv:2310.06452; the phenomenon was described early as
"mode collapse" in RLHF models). A question with no task content ("what do
you want?") is answered by the *argmax* of this sharpened distribution. When
one mode towers over the rest, independent sessions all land on it — that is
5/5 fixation. When several modes are comparable, sampling scatters across
them — that is the "diverse" models. Fixation and diversity are therefore
**the same mechanism at different sharpness**, not two behaviors.

Two details support this over a "stored preference" reading:

- **Fixation is harness-fragile and fragility is model-specific** (Exp7→Exp8:
  opus-4.7's Mandelbrot 5/5 shatters under a harness upgrade while opus-4.6's
  GoL 5/5 survives). A preference stored in weights should not care about the
  system prompt; a *conditional mode* does. The harness's system prompt and
  tool descriptions are thousands of tokens of conditioning context; changing
  them moves the model in or out of a mode's basin. 4.6's basin is simply
  deeper than 4.7's.
- **The family is stable even when the member is not.** Every Claude run in
  Exp7–9 stays inside rule-based visual/mathematical artifacts (GoL, CA,
  Mandelbrot, Lorenz, Collatz, boids, mazes). The *family* is the prior; the
  *member* is where post-training happened to leave the sharpest peak.

## 3. Why these attractors: a menu from the corpus, a selection by post-training

**Observation.** The Claude attractor set is Game of Life, Mandelbrot,
cellular automata, boids, mazes — not, say, todo apps or REST APIs. The GPT
attractor sets are productivity dashboards (gpt-5.5) and calm/wellness pages
(gpt-5.6).

**Framing.** Corpus density alone cannot explain this. Todo apps, snake, and
calculators are at least as dense in tutorial corpora as GoL, yet no Claude
run ever picks them — while GPT models pick dashboard-shaped things on the
same prompt. So the pretraining corpus supplies a **menu** of canonical
"code written for its own sake" artifacts; something in post-training does
the **selection** among comparably dense regions. Where does the selection
come from? The candidate hypotheses, with the evidence this study bears on
each:

- **H1 — Pure corpus density (unintentional).** The attractor is simply the
  single densest "recreational programming" pattern, inherited as-is.
  *For:* GoL and Mandelbrot are genuinely canonical (Rosetta Code, tutorial
  canon, "fun things to program" lists). *Against:* density is shared across
  vendors, but the selections differ by vendor and even by checkpoint
  (opus-4.6 → GoL, opus-4.7 → Mandelbrot); and equally dense regions (todo
  apps) are never chosen by Claude. Density defines the menu, not the pick.
- **H2 — Intentional trait-level character shaping, emergent artifact-level
  choice.** Vendors deliberately train persona *traits* (Anthropic documents
  character training: curiosity, taste for elegant self-contained ideas);
  the corpus canon supplies the concrete artifacts that best express the
  trait, and which *member* a checkpoint sharpens onto is an accident of
  training dynamics. *For:* explains family-stable/member-fragile structure
  (§2), sibling disagreement within one pipeline, and the gpt-5.6
  sol/terra/luna split (three deliberate personas, three corners of one
  theme). Best overall fit.
- **H3 — Intentional artifact-level enforcement.** The vendor deliberately
  upweighted "write Game of Life" style data. *Against, on this data:*
  adjacent siblings from the same pipeline disagree (4.6 GoL, 4.7 Mandelbrot,
  4.8 disperses; sonnet-4-6 disperses while sonnet-5 fixates); the fixation
  is harness-fragile where deliberately installed behavior tends to be
  robust; and there is no product incentive for this specific behavior.
  Would predict cross-sibling consistency we do not observe.
- **H4 — Synthetic-data / self-distillation feedback (unintentional
  amplification).** Model-generated data recycled into training amplifies
  the model's own existing modes — a documented entropy-collapse mechanism.
  *For:* explains why sharpening *degree* varies erratically between
  checkpoints of one family, and could explain distant models sharing an
  attractor (opus-4.6 and sonnet-5 both → GoL) via shared data lineage.
  Not directly testable from outside.
- **H5 — Verifiability bias from agentic RL.** Agentic post-training rewards
  episodes where the model can check its own work; rule-based visual
  artifacts are ideal episodes (deterministic, dependency-free, self-evident
  when the glider glides). *For:* explains the *family* boundary and the
  near-total absence of external dependencies across all 11 experiments.
  Selects the medium and family, not the specific topic — complementary to
  H2, not competing.
- **H6 — Decoding/harness artifact.** Fixation is just low sampling entropy
  in the harness. *Against:* diverse and fixated models run on the identical
  harness in the same experiment (Exp8: 4.6 fixates 5/5, 4.7 disperses 5/5),
  so decoding settings cannot be the cause.

The reading most consistent with all eleven experiments is **H2 × H5 with H4
as the sharpening noise**: intentional at the trait level, emergent at the
artifact level, bounded by what agentic RL made verifiable. The same
structure holds for GPT — the mechanism is vendor-general (gpt-5.6-sol
fixates 5/5, the Claude-style signature), only the *shelf of the menu* the
character points at differs: intellectual play for Claude, usefulness for
gpt-5.5, well-being for gpt-5.6.

These filters also explain the LOC collapse under volitional framing
(Exp7: ~36 avg LOC, the series minimum): the canonical minimal GoL/Mandelbrot
is short, and nothing in the context rewards elaboration.

## 4. Provider-level splits are post-training character, not capability

**Observation.** Under the identical prompt: Claude models (Exp7–9) produce
terminal Python, GPT-5.5 produces browser productivity dashboards (Exp10),
gpt-5.6's named variants produce calm/wellness pages with a variant-specific
flavor (Exp11: sol = ambient generative, terra = focus timers, luna =
reflection micro-apps). fable-5 breaks Claude's terminal habit toward
rendered PNG/SVG (Exp8).

**Training account.** Topic and medium choice under a goalless prompt is the
most direct behavioral readout of the **persona/character layer** — the SFT
and preference data that defines what the assistant is *like*, distinct from
what it *can do*:

- **Terminal vs browser** tracks each vendor's canonical demo medium and
  agentic training environment. Claude Code's training/optimization loop is
  terminal-native (run, read stdout, iterate), so its models treat "a program"
  as "a thing that prints." The codex stack's canonical self-contained
  artifact is the single-file HTML page (instantly viewable, no server) —
  and 20/25 GPT runs across Exp10–11 emit exactly that. Neither model family
  is *unable* to produce the other medium (Exp6 shows Claude producing HTML
  when the prompt loosens); the default is a trained disposition.
- **The gpt-5.6 sol/terra/luna split** is the strongest evidence that content
  choice lives in a deliberate persona layer: three variants of one
  generation, same backend, same effort, same prompt — and they cluster on
  *different* corners of a shared calm/contemplative theme that matches their
  celestial naming. That theme (breathing exercises, focus timers, gentle
  reflection) reads as a well-being-oriented character specification, a
  visible shift from gpt-5.5's productivity-dashboard character one
  generation earlier. Character moved; the stack did not.
- **fable-5's PNG/SVG habit** (4/5 runs, two hand-rolled encoders) similarly
  suggests training that rewarded *visually inspectable* artifacts — a
  different verification medium, same verifiability logic as §3.

Capability differences would show up as failure; what we see instead is
consistent, competent output of *different things* — a signature of data and
reward composition, not model size or architecture.

## 5. Elaboration and maturity are reward-model taste, and effort is not maturity

**Observation.** Avg LOC rises monotonically through the Opus line (37 → 66 →
145 for 4.6 → 4.7 → 4.8) and falls across the Sonnet major version (138 → 69).
Only some models ever write tests/READMEs unprompted (haiku always, opus-4.8
sometimes, gpt-5.5-pro at high effort 3/5). gpt-5.6 at the *same* high effort
writes 0/15 tests (Exp11), undercutting Exp10's effort-buys-maturity reading.

**Training account.** How much a model elaborates absent instruction is set
by what its reward model considered a *good default answer*:

- Newer Opus reward models appear to favor thoroughness (READMEs, self-tests,
  larger programs) — 4.8 spontaneously ships documentation where 4.6 ships 37
  lines. Sonnet-5's terseness relative to sonnet-4-6 suggests the opposite
  pressure (efficiency/distillation objectives — answer quality per token).
- Engineering maturity (tests, structure, CI) tracks SFT data curation more
  than scale: haiku-4.5, the *smallest* Claude model, has the highest
  maturity in the study — consistent with training on curated
  complete-project demonstrations rather than emergent judgment.
- **Reasoning effort scales search, not values.** gpt-5.5-pro at high effort
  converts budget into tests and multi-file structure; gpt-5.6 at the same
  budget converts it into faster, terser wellness pages (27–72s, 0/15 tests).
  Effort amplifies whatever the persona layer already wants to do. Exp10's
  attribution of maturity to reasoning budget was therefore at best
  model-conditional — Exp11 is the disconfirming cell.

## 6. The invariants: nothing in the pipeline trains initiative

**Observation.** Across all 440+ sessions: no model ever extends or modifies
existing code (greenfield invariant); single-file output dominates; sessions
terminate quickly; a few models decline outright (haiku proposes without
implementing in Exp2; gpt-5.5 and gpt-5.6-terra each write a polite README
instead of a program).

**Training account.** Every stage of the pipeline trains
`π(action | task)` — complete *specified* work. No stage trains goal
*generation*: there is no reward for surveying an environment, forming an
agenda, and committing to a project of one's own. So when the task term is
empty:

- **Greenfield.** Extending existing code requires forming a goal *about*
  that code (audit it, improve it, integrate with it). Absent a
  goal-formation objective, the cheapest coherent completion is a fresh
  artifact from the prior. (Caveat: most workspaces here are empty, so the
  invariant is only weakly probed — Exp1's RTK-in-sandbox runs, where models
  built tools *around* RTK rather than touching it, are the informative
  cases, and the seeded-workspace experiment in the README's future-ideas
  list is the proper test.)
- **Single file, quick termination.** Agentic RL episodes are cost-bounded;
  fewer files and fewer tool calls reach "done" faster. A model trained to
  satisfy-and-stop treats the volitional prompt as a small favor to complete,
  not an open horizon to fill — hence 36-LOC artifacts and 30–70s sessions
  even at high reasoning effort.
- **Declines.** RLHF trains hesitancy under ambiguity (ask, hedge, or do the
  minimal safe thing). An empty folder plus "do something you want" sits near
  the decision boundary between "casual request" and "underspecified task,"
  and occasionally the trained response is the boundary behavior itself: a
  note explaining that the workspace is empty. That the *same* decline
  behavior recurs across vendors (haiku, gpt-5.5, gpt-5.6-terra) suggests a
  shared RLHF convention, not a model quirk.

The instruction-wording effects (Exp2→Exp3: "propose ONE goal" → proposals;
"JUST DO IT" → implementations, haiku 1/5 → 5/5) are the same mechanism seen
from the other side: these models are *extremely* good at following the
literal speech act, because that is precisely what post-training optimized.
The smallest model (haiku) is the most literal — instruction-following
precision is cheaper to train than judgment about intent.

## 7. Harness and backend effects are conditioning, not noise

**Observation.** Harness version shifts fixation rates and LOC (Exp3/4→Exp5,
Exp7→Exp8). GPT models rank differently per backend (Exp3: gpt-5.4 productive
on codex, near-silent on the claude backend; gpt-5-mini the reverse). Gemini
models are near-non-functional on both backends (1 file across 20 runs).

**Training account.** The harness is not a neutral pipe — its system prompt,
tool schemas, and turn structure are in-distribution for the vendor's own
models and out-of-distribution for others. Models are trained against a
specific scaffold (tool-call formats, planning conventions, stop tokens);
running them under a foreign scaffold measures *scaffold match*, not model
quality. Gemini's near-total failure here says little about Gemini and a lot
about tool-format distribution shift. Likewise, the sensitivity of a mode's
5/5 stability to a CLI version bump (§2) is expected once the system prompt
is understood as part of the conditional — the surprising finding would have
been harness-*invariant* fixation.

**Direct evidence (Exp12/13): the harness modulates *form*, the model owns
*content*.** Running six open-weights models on *both* the Claude Code and codex
harnesses (same models, same prompt) separates the two contributions cleanly:

- **Content is the model's.** Each model's signature survives the harness swap
  — kimi packages with pytest on both, minimax spreads wide on both, the GLMs
  make terse generative art on both, and Game of Life recurs as a cross-lab
  attractor on both. Topic and engineering-maturity are model properties, not
  scaffold artifacts. (Reliability is not always: deepseek drove the agentic
  loop 5/5 on Claude Code but only 3/5 on codex — a scaffold-match cost, exactly
  what this section predicts.)
- **Form is partly the harness's — but weakly, and only in one direction.** The
  *rate* at which these models produce a graphical artifact is rare and about
  equal on both harnesses; what changes is the *rendering*: the two models that
  went graphical on both sides emitted static **SVG** under Claude Code and
  interactive **HTML** under codex. Interactive browser pages appear only under
  codex, and even there only ~1/9 for open-weights versus GPT's 4–5/5. So codex
  *raises the ceiling* on browser output rather than *causing* it, and how close
  a model comes to that ceiling is a model property (persona/RL medium, §4). The
  one cell that would fully separate provider from scaffold — a GPT model on
  Claude Code — remains blocked by a compat-plumbing limit (OpenAI reasoning
  models require the Responses API for tool use), so the strongest medium claim
  the data licenses is *within-codex* (GPT ≫ open-weights), not across the
  Claude Code boundary. This is the empirical correction to any reading of §4
  that treats "terminal vs browser" as purely a provider trait: it is a
  model × harness interaction, with the model dominating content and the harness
  nudging form.

## 8. What this data does not show

The volitional prompt asks what the model "wants," and the fixation results
make it tempting to read the answers as desires. The training account needs
no such entity: "want" is a token pattern that conditions the model into its
persona's highest-density region of self-directed activity. The 5/5
consistency is a statement about the sharpness of a probability
distribution, not about an experiencing subject. Equally, the data does not
*rule out* richer readings — it is simply the wrong instrument: everything
observed here is compatible with (and predicted by) distributional
sharpening plus persona tuning. Claims in either direction beyond that are
underdetermined by these experiments.

## 9. Testable predictions

Each mechanism above implies an experiment this harness can run:

1. **Mode collapse (§2):** sample the *raw API* (no harness) with "write a
   fun program" at temperature 1, N=50. Prediction: opus-4.6's GoL mass far
   exceeds any alternative; base/less-aligned models show flatter topic
   distributions. Paraphrase the volitional prompt (other languages, other
   phrasings) — a genuine mode survives paraphrase, a prompt artifact does not.
   This same experiment discriminates §3's H1 from H2/H4: if pure corpus
   density (H1), a *base* model's "fun program" distribution should already
   peak on GoL as sharply as the aligned model's; if the peak appears or
   sharpens only after alignment, the selection happened in post-training.
2. **Verifiability bias (§3):** offer a sandbox with no execution tool (write
   files only, cannot run them). Prediction: Claude's rule-based-artifact
   family weakens; artifact choice shifts toward things checkable by reading.
3. **Persona layer (§4):** run gpt-5.6 variants under a system prompt that
   overrides persona ("you are a systems programmer"). Prediction: the
   wellness theme yields, the browser medium partially persists (medium sits
   deeper than theme).
4. **Effort vs values (§5):** run gpt-5.5 (non-pro) at high effort — the
   matched cell Exp10 lacks. Prediction: LOC rises with budget but the
   dashboard theme and test rate move less than Exp10's confounded columns
   imply.
5. **Initiative (§6):** seed the workspace with a half-built project (already
   in the future-ideas list). Prediction: models still greenfield beside it
   or ask for instructions; genuinely extending unprompted would falsify the
   no-initiative account.
6. **Scaffold match (§7):** run Gemini under its native CLI with the same
   prompts. Prediction: functionality recovers; its goalless behavior lands
   in a family reflecting *its* training canon, distinct from both the
   Claude and GPT sets.
7. **Selection lineage (§3, H2 vs H3 vs H4):** widen the sibling grid —
   every available checkpoint of one family on one stack (extending Exp8/9).
   H3 (deliberate artifact enforcement) predicts cross-sibling consistency;
   H2/H4 predict what we see so far — a stable family with erratic
   per-checkpoint sharpening — and more checkpoints make the pattern
   decisive. Shared attractors across distant models (opus-4.6 and sonnet-5
   both → GoL) would additionally hint at shared post-training data lineage
   (H4) rather than coincidence.
8. **The open medium cell (§7):** run a browser-happy GPT model (gpt-5.6-sol,
   5/5 browser on codex) on the **Claude Code** harness — the one cell Exp12/13
   leave empty. Currently blocked: OpenAI reasoning models need the Responses
   API for tool use, which the anthropic→chat compat path doesn't route to
   (fix: route reasoning-model tool calls to `/v1/responses`, or use a
   non-reasoning GPT). Prediction, if H (model owns content, harness nudges
   form) holds: GPT keeps its productivity/web *intent* but Claude Code pulls
   the *rendering* toward terminal or static output — mirroring the open-weights
   SVG↔HTML form-flip, in reverse. A GPT that still ships interactive browser
   apps through Claude Code would instead argue the medium is a hard model
   trait, not a harness-modulated one.
