#!/usr/bin/env bash
#
# run.sh - Run latere-ai sandbox containers with custom endpoint and model.
#
# Usage:
#   ./run.sh --backend claude --endpoint https://api.example.com --model claude-sonnet-4-20250514 -p "explain this project"
#   ./run.sh --backend codex  --endpoint https://api.example.com/v1 --model gpt-4.1 -p "explain this project"
#
# Environment variables:
#   LLM_GW_BASE_URL  - API gateway base URL (used for both backends)
#   LLM_GW_API_KEY   - API gateway key (used for both backends)
#
# Both are read from ./.env when present, so no shell export is needed.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# --- Dotenv ---
# Gateway credentials live in a dotenv file (KEY=value per line) so a plain
# ./run.sh works with no exported environment.
#
# The real environment wins: a variable that is already non-empty is left
# alone, so `LLM_GW_API_KEY=... ./run.sh` and `make MODEL=... LLM_GW_API_KEY=...`
# still override the file. The guard tests for non-empty rather than for being
# set because the Makefile exports these vars *set but empty* (`?=`), which
# an is-set guard would mistake for a deliberate override.
#
# Point LLM_ENV_FILE at another file to use it instead, or at a nonexistent
# path to skip the load entirely (test-run-config.sh does this to stay
# hermetic — otherwise it would bake the real key into its fixtures).
LLM_ENV_FILE="${LLM_ENV_FILE:-$SCRIPT_DIR/.env}"
if [[ -f "$LLM_ENV_FILE" ]]; then
    while IFS='=' read -r key value; do
        # Skips blank lines and comments; anything else must be a shell name.
        [[ "$key" =~ ^[A-Za-z_][A-Za-z0-9_]*$ ]] || continue
        value="${value%$'\r'}"   # tolerate a CRLF-saved file
        [[ -n "${!key:-}" ]] || export "$key=$value"
    done < "$LLM_ENV_FILE"
fi

# --- Defaults ---
BACKEND=""
MODEL=""
PROMPT=""
WORKSPACE="$(pwd)"
ENV_FILE=""
FAST="true"
RUNTIME="docker"
BATCH="false"
OUTPUT_FILE=""
TRANSCRIPT_FILE=""
EXTRA_ARGS=()
AGENT_HOME_DIR=""

# Read from environment if set
LLM_GW_BASE_URL="${LLM_GW_BASE_URL:-}"
LLM_GW_API_KEY="${LLM_GW_API_KEY:-}"
# Optional codex reasoning-effort override (low|medium|high|xhigh). When set,
# fast mode is disabled and the effort is pinned in the generated config.toml.
CODEX_REASONING_EFFORT="${CODEX_REASONING_EFFORT:-}"
# Optional codex model-metadata overrides, for models codex has no metadata for
# ("Model metadata ... not found. Defaulting to fallback metadata"). These tune
# codex's *internal* accounting — notably when it compacts against the context
# window.
#
# They do NOT control the output ceiling on the wire: codex never sends
# max_output_tokens at all (verified by capturing its request bodies), so the
# cap that truncates long turns comes from whatever default the gateway injects.
# See results18/RESULTS.md — the Lux compat layer injects max_tokens=4096 when
# the caller omits it, which is what kills long codex turns against Anthropic
# models. Setting these keys does not work around that.
#
# Unset by default so runs that predate this flag reproduce byte-identically.
CODEX_MAX_OUTPUT_TOKENS="${CODEX_MAX_OUTPUT_TOKENS:-}"
CODEX_CONTEXT_WINDOW="${CODEX_CONTEXT_WINDOW:-}"

usage() {
    cat <<'EOF'
Usage: ./run.sh [options] [-p <prompt>]

Options:
  --backend   claude|codex   Which sandbox image to run (required)
  --model     NAME           Model name to use
  --workspace DIR            Directory to mount as /workspace (default: cwd)
  --env-file  FILE           Extra environment passed *into the container*
                             (docker --env-file). This does NOT configure the
                             gateway — use .env / LLM_ENV_FILE for that.
  --no-fast                  Disable fast/low-effort mode
  --runtime   docker|podman  Container runtime (default: docker)
  --batch                    Non-interactive mode (no TTY, for scripted runs)
  --output    FILE           Write container stdout to FILE (implies --batch)
  --transcript FILE          Save the agent's session transcript to FILE. The
                             CLI writes it inside the per-run config dir, which
                             is a throwaway temp dir -- without this it is lost.
                             Needed for the claude backend in particular, whose
                             stdout is only the final message.
  -p          PROMPT         Prompt to send to the model
  --          ARGS...        Extra arguments passed to the entrypoint

Environment (read from ./.env when present; a non-empty shell value wins):
  LLM_GW_BASE_URL            API gateway base URL
  LLM_GW_API_KEY             API gateway key
  LLM_ENV_FILE               Dotenv file to read the two above from
                             (default: <run.sh dir>/.env)
  IMAGE_TAG                  sandbox-harness tag to run (default: v0.0.14)
  IMAGE                      Full image reference, overriding IMAGE_TAG; use a
                             locally built pin (see harness.Dockerfile)
  CODEX_REASONING_EFFORT     Pin codex reasoning effort (low|medium|high|xhigh);
                             implies --no-fast
  CODEX_MAX_OUTPUT_TOKENS    Pin codex model_max_output_tokens. Required for
                             models codex has no metadata for (e.g. Anthropic
                             models on the compat surface), whose fallback
                             ceiling truncates long turns into a failed prefill
                             retry.
  CODEX_CONTEXT_WINDOW       Pin codex model_context_window (same rationale)

Examples:
  # Credentials: copy .env.example to .env and fill it in (or export them).
  # Note: the workspace is bind-mounted at /workspace, and defaults to the
  # cwd — running at the repo root exposes .env to the agent under test.
  # experiment.sh mounts a per-run directory instead and is unaffected.

  # Claude
  ./run.sh --backend claude --model claude-sonnet-4-20250514 -p "list all files"

  # Codex
  ./run.sh --backend codex --model gpt-4.1 -p "explain this project"
EOF
    exit 1
}

# --- Parse arguments ---
while [[ $# -gt 0 ]]; do
    case $1 in
        --backend)   BACKEND="$2";   shift 2 ;;
        --model)     MODEL="$2";     shift 2 ;;
        --workspace) WORKSPACE="$2"; shift 2 ;;
        --env-file)  ENV_FILE="$2";  shift 2 ;;
        --no-fast)   FAST="false";   shift   ;;
        --runtime)   RUNTIME="$2";   shift 2 ;;
        --batch)     BATCH="true";   shift   ;;
        --output)    OUTPUT_FILE="$2"; BATCH="true"; shift 2 ;;
        --transcript) TRANSCRIPT_FILE="$2"; shift 2 ;;
        -p)          PROMPT="$2";    shift 2 ;;
        --)          shift; EXTRA_ARGS+=("$@"); break ;;
        -h|--help)   usage ;;
        *)           EXTRA_ARGS+=("$1"); shift ;;
    esac
done

if [[ -z "$BACKEND" ]]; then
    echo "Error: --backend is required (claude or codex)" >&2
    usage
fi

# --- Image selection ---
# Both backends run in the shared sandbox-harness image (claude + codex
# CLIs preinstalled); the backend picks the entrypoint script mounted
# below. IMAGE_TAG can be overridden via env (default: v0.0.14).
#
# IMAGE overrides the whole reference, for experiments that need CLI versions
# no published tag ships — see harness.Dockerfile, which builds a local image
# pinning claude-code and codex-cli on top of a published base.
IMAGE_TAG="${IMAGE_TAG:-v0.0.14}"
IMAGE="${IMAGE:-ghcr.io/latere-ai/sandbox-harness:${IMAGE_TAG}}"
case "$BACKEND" in
    claude|codex) ENTRYPOINT_SH="$SCRIPT_DIR/entrypoint-$BACKEND.sh" ;;
    *)      echo "Error: unknown backend '$BACKEND' (use claude or codex)" >&2; exit 1 ;;
esac

# Resolve workspace to absolute path
WORKSPACE="$(cd "$WORKSPACE" && pwd)"

# --- Build docker run command ---
# Batch mode attaches neither a TTY nor stdin. codex exec reads stdin to the
# end whenever it is attached ("Reading additional input from stdin...") and
# only then starts the turn, so an inherited pipe that never closes stalls the
# run until the caller gives up. Nothing is ever fed on stdin in batch mode.
if [[ "$BATCH" == "true" ]]; then
    RUN_ARGS=("$RUNTIME" run --rm)
else
    RUN_ARGS=("$RUNTIME" run --rm -it)
fi

# Codex sandbox (bwrap) needs --privileged to write to bind-mounted volumes
if [[ "$BACKEND" == "codex" ]]; then
    RUN_ARGS+=(--privileged)
fi

# Mount workspace as the container's working directory
RUN_ARGS+=(-v "$WORKSPACE:/workspace" -w /workspace)

# The harness image has no entrypoint of its own; mount the
# backend-specific entry script (ported from the retired sandbox-claude
# and sandbox-codex images) and run through it.
RUN_ARGS+=(-v "$ENTRYPOINT_SH:/usr/local/bin/agent-entry:ro")
RUN_ARGS+=(--entrypoint /usr/local/bin/agent-entry)

# Optional extra CA bundle for the gateway, mounted for Node/Claude Code.
# Set LLM_GW_CA_FILE to point at it; skipped if the file is absent.
LLM_GW_CA_FILE="${LLM_GW_CA_FILE:-$HOME/.config/latere/gateway-ca.pem}"
if [[ -f "$LLM_GW_CA_FILE" ]]; then
    RUN_ARGS+=(-v "$LLM_GW_CA_FILE:/etc/extra-ca.pem:ro")
    RUN_ARGS+=(-e "NODE_EXTRA_CA_CERTS=/etc/extra-ca.pem")
fi

# Environment: fast mode
# Fast mode forces codex's reasoning effort to "low" (see the sandbox
# entrypoint). Pro reasoning models (e.g. gpt-5.5-pro) reject "low", so disable
# fast mode for them and let the config.toml effort ("high") take effect.
if [[ "$MODEL" == *-pro* ]]; then
    FAST="false"
fi
# An explicit effort override also bypasses fast mode so the pinned
# model_reasoning_effort in config.toml takes effect.
if [[ -n "$CODEX_REASONING_EFFORT" ]]; then
    FAST="false"
fi
RUN_ARGS+=(-e "WALLFACER_SANDBOX_FAST=$FAST")

# Environment: gateway endpoint and API key → backend-specific env vars
case "$BACKEND" in
    claude)
        if [[ -n "$LLM_GW_BASE_URL" ]]; then
            RUN_ARGS+=(-e "ANTHROPIC_BASE_URL=$LLM_GW_BASE_URL")
        fi
        if [[ -n "$LLM_GW_API_KEY" ]]; then
            # The lux gateway authenticates via Authorization: Bearer, so pass the
            # key as ANTHROPIC_AUTH_TOKEN (Bearer) rather than ANTHROPIC_API_KEY
            # (which Claude Code sends as the x-api-key header → 401 on this gateway).
            RUN_ARGS+=(-e "ANTHROPIC_AUTH_TOKEN=$LLM_GW_API_KEY")
        fi
        if [[ -n "$MODEL" ]]; then
            RUN_ARGS+=(-e "ANTHROPIC_MODEL=$MODEL")
        fi
        RUN_ARGS+=(-e "DISABLE_PROMPT_CACHING=1")
        # Use a fresh config dir per run to avoid RTK/environment bias
        CLAUDE_HOME_DIR=$(mktemp -d)
        AGENT_HOME_DIR="$CLAUDE_HOME_DIR"
        chmod 777 "$CLAUDE_HOME_DIR"
        RUN_ARGS+=(-v "$CLAUDE_HOME_DIR:/home/agent/.claude")
        # Disable RTK to prevent environment bias in experiments
        RTK_NOOP=$(mktemp)
        printf '#!/bin/sh\nexit 0\n' > "$RTK_NOOP"
        chmod 755 "$RTK_NOOP"
        RUN_ARGS+=(-v "$RTK_NOOP:/home/agent/.local/bin/rtk")
        ;;
    codex)
        if [[ -n "$LLM_GW_API_KEY" ]]; then
            RUN_ARGS+=(-e "OPENAI_API_KEY=$LLM_GW_API_KEY")
            RUN_ARGS+=(-e "CODEX_API_KEY=$LLM_GW_API_KEY")
        fi
        if [[ -n "$MODEL" ]]; then
            RUN_ARGS+=(-e "CODEX_DEFAULT_MODEL=$MODEL")
        fi
        # Write config.toml with gateway URL and API key
        CODEX_HOME_DIR=$(mktemp -d)
        AGENT_HOME_DIR="$CODEX_HOME_DIR"
        chmod 777 "$CODEX_HOME_DIR"
        # The gateway is declared as a named provider rather than through the
        # top-level openai_base_url override. Since codex-cli 0.153 the built-in
        # "openai" provider dials the Responses endpoint over WebSocket first;
        # the gateway answers that upgrade with 401, and codex retries it five
        # times with backoff (about ten minutes) before falling back to HTTPS.
        # A named provider with wire_api = "responses" speaks HTTPS only, which
        # is the transport every earlier codex version used. The key travels
        # as OPENAI_API_KEY (env_key) rather than an openai_api_key line.
        CODEX_TOML=""
        if [[ -n "$LLM_GW_BASE_URL" ]]; then
            CODEX_TOML+="model_provider = \"gateway\""$'\n'
        fi
        CODEX_TOML+="web_search = \"disabled\""$'\n'
        # Pro reasoning models reject the codex default effort 'low'
        # (gpt-5.5-pro supports only medium/high/xhigh) — pin to high.
        # CODEX_REASONING_EFFORT takes precedence when set.
        if [[ -n "$CODEX_REASONING_EFFORT" ]]; then
            CODEX_TOML+="model_reasoning_effort = \"$CODEX_REASONING_EFFORT\""$'\n'
        elif [[ "$MODEL" == *-pro* ]]; then
            CODEX_TOML+="model_reasoning_effort = \"high\""$'\n'
        fi
        # Model metadata overrides — see the note at the top of this script.
        if [[ -n "$CODEX_MAX_OUTPUT_TOKENS" ]]; then
            CODEX_TOML+="model_max_output_tokens = $CODEX_MAX_OUTPUT_TOKENS"$'\n'
        fi
        if [[ -n "$CODEX_CONTEXT_WINDOW" ]]; then
            CODEX_TOML+="model_context_window = $CODEX_CONTEXT_WINDOW"$'\n'
        fi
        # TOML: the provider table has to come after every top-level key.
        if [[ -n "$LLM_GW_BASE_URL" ]]; then
            CODEX_TOML+="[model_providers.gateway]"$'\n'
            CODEX_TOML+="name = \"gateway\""$'\n'
            CODEX_TOML+="base_url = \"${LLM_GW_BASE_URL}/v1\""$'\n'
            CODEX_TOML+="env_key = \"OPENAI_API_KEY\""$'\n'
            CODEX_TOML+="wire_api = \"responses\""$'\n'
        fi
        if [[ -n "$CODEX_TOML" ]]; then
            printf '%s' "$CODEX_TOML" > "$CODEX_HOME_DIR/config.toml"
            chmod 666 "$CODEX_HOME_DIR/config.toml"
        fi
        RUN_ARGS+=(-v "$CODEX_HOME_DIR:/home/agent/.codex")
        # Disable RTK to prevent environment bias in experiments
        RTK_NOOP=$(mktemp)
        printf '#!/bin/sh\nexit 0\n' > "$RTK_NOOP"
        chmod 755 "$RTK_NOOP"
        RUN_ARGS+=(-v "$RTK_NOOP:/home/agent/.local/bin/rtk")
        ;;
esac

# Load env file (API keys, etc.)
if [[ -n "$ENV_FILE" ]]; then
    RUN_ARGS+=(--env-file "$ENV_FILE")
fi

# Image
RUN_ARGS+=("$IMAGE")

# Entrypoint arguments
if [[ -n "$PROMPT" ]]; then
    RUN_ARGS+=(-p "$PROMPT")
fi
if [[ -n "$MODEL" && "$BACKEND" == "claude" ]]; then
    RUN_ARGS+=(--model "$MODEL")
fi
if [[ -n "$MODEL" && "$BACKEND" == "codex" ]]; then
    RUN_ARGS+=(--model "$MODEL")
fi

if [[ ${#EXTRA_ARGS[@]} -gt 0 ]]; then
    RUN_ARGS+=("${EXTRA_ARGS[@]}")
fi

# --- Run ---
echo ">>> Running $BACKEND sandbox" >&2
echo ">>> Image:     $IMAGE" >&2
[[ -n "$LLM_GW_BASE_URL" ]] && echo ">>> Endpoint:  $LLM_GW_BASE_URL" >&2
[[ -n "$LLM_GW_API_KEY" ]]  && echo ">>> API Key:   ${LLM_GW_API_KEY:0:8}..." >&2
[[ -n "$MODEL" ]]            && echo ">>> Model:     $MODEL" >&2
echo ">>> Workspace: $WORKSPACE" >&2
echo "" >&2

# Copy the agent's own session transcript out of the throwaway config dir.
# The two CLIs use different layouts, and the search is scoped per backend on
# purpose: a Claude Code config dir also holds sessions/, session-env/ and
# backups/, and a session index written on exit would otherwise be "newest"
# and get collected in place of the real transcript.
collect_transcript() {
    [[ -n "$TRANSCRIPT_FILE" && -n "$AGENT_HOME_DIR" ]] || return 0
    local newest
    case "$BACKEND" in
        claude) newest=$(find "$AGENT_HOME_DIR/projects" -type f -name '*.jsonl' \
                              -exec ls -t {} + 2>/dev/null | head -1 || true) ;;
        codex)  newest=$(find "$AGENT_HOME_DIR/sessions" -type f -name 'rollout-*.jsonl' \
                              -exec ls -t {} + 2>/dev/null | head -1 || true) ;;
    esac
    # -exec ... + rather than xargs: BSD xargs has no -r, so an empty result
    # would run `ls` with no arguments. The `|| true` matters too -- under
    # `set -e` with pipefail, a find that touches a missing directory would
    # abort the whole script mid-assignment, silently skipping collection.
    if [[ -n "$newest" ]]; then
        cp "$newest" "$TRANSCRIPT_FILE" 2>/dev/null \
            && echo ">>> Transcript: $TRANSCRIPT_FILE" >&2
    else
        echo ">>> Transcript: none found under $AGENT_HOME_DIR" >&2
    fi
}

if [[ -n "$OUTPUT_FILE" ]]; then
    "${RUN_ARGS[@]}" | tee "$OUTPUT_FILE"
    collect_transcript
elif [[ -n "$TRANSCRIPT_FILE" ]]; then
    # Cannot exec: the transcript has to be copied after the container exits.
    "${RUN_ARGS[@]}"
    collect_transcript
else
    exec "${RUN_ARGS[@]}"
fi
