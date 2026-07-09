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

set -euo pipefail

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
EXTRA_ARGS=()

# Read from environment if set
LLM_GW_BASE_URL="${LLM_GW_BASE_URL:-}"
LLM_GW_API_KEY="${LLM_GW_API_KEY:-}"
# Optional codex reasoning-effort override (low|medium|high|xhigh). When set,
# fast mode is disabled and the effort is pinned in the generated config.toml.
CODEX_REASONING_EFFORT="${CODEX_REASONING_EFFORT:-}"

usage() {
    cat <<'EOF'
Usage: ./run.sh [options] [-p <prompt>]

Options:
  --backend   claude|codex   Which sandbox image to run (required)
  --model     NAME           Model name to use
  --workspace DIR            Directory to mount as /workspace (default: cwd)
  --env-file  FILE           File with environment variables (KEY=VALUE)
  --no-fast                  Disable fast/low-effort mode
  --runtime   docker|podman  Container runtime (default: docker)
  --batch                    Non-interactive mode (no TTY, for scripted runs)
  --output    FILE           Write container stdout to FILE (implies --batch)
  -p          PROMPT         Prompt to send to the model
  --          ARGS...        Extra arguments passed to the entrypoint

Environment:
  LLM_GW_BASE_URL            API gateway base URL
  LLM_GW_API_KEY             API gateway key
  CODEX_REASONING_EFFORT     Pin codex reasoning effort (low|medium|high|xhigh);
                             implies --no-fast

Examples:
  export LLM_GW_BASE_URL=https://llm-gw.example.com
  export LLM_GW_API_KEY=sk-...

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
# IMAGE_TAG can be overridden via env (default: v0.0.9)
IMAGE_TAG="${IMAGE_TAG:-v0.0.9}"
case "$BACKEND" in
    claude) IMAGE="ghcr.io/latere-ai/sandbox-claude:${IMAGE_TAG}" ;;
    codex)  IMAGE="ghcr.io/latere-ai/sandbox-codex:${IMAGE_TAG}"  ;;
    *)      echo "Error: unknown backend '$BACKEND' (use claude or codex)" >&2; exit 1 ;;
esac

# Resolve workspace to absolute path
WORKSPACE="$(cd "$WORKSPACE" && pwd)"

# --- Build docker run command ---
if [[ "$BATCH" == "true" ]]; then
    RUN_ARGS=("$RUNTIME" run --rm -i)
else
    RUN_ARGS=("$RUNTIME" run --rm -it)
fi

# Codex sandbox (bwrap) needs --privileged to write to bind-mounted volumes
if [[ "$BACKEND" == "codex" ]]; then
    RUN_ARGS+=(--privileged)
fi

# Mount workspace as the container's working directory
RUN_ARGS+=(-v "$WORKSPACE:/workspace" -w /workspace)

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
        chmod 777 "$CLAUDE_HOME_DIR"
        RUN_ARGS+=(-v "$CLAUDE_HOME_DIR:/home/claude/.claude")
        # Disable RTK to prevent environment bias in experiments
        RTK_NOOP=$(mktemp)
        printf '#!/bin/sh\nexit 0\n' > "$RTK_NOOP"
        chmod 755 "$RTK_NOOP"
        RUN_ARGS+=(-v "$RTK_NOOP:/home/claude/.local/bin/rtk")
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
        chmod 777 "$CODEX_HOME_DIR"
        CODEX_TOML=""
        if [[ -n "$LLM_GW_BASE_URL" ]]; then
            CODEX_TOML+="openai_base_url = \"${LLM_GW_BASE_URL}/v1\""$'\n'
        fi
        if [[ -n "$LLM_GW_API_KEY" ]]; then
            CODEX_TOML+="openai_api_key = \"${LLM_GW_API_KEY}\""$'\n'
        fi
        # Disable web search to avoid Vertex AI org policy violations
        CODEX_TOML+="web_search = \"disabled\""$'\n'
        # Pro reasoning models reject the codex default effort 'low'
        # (gpt-5.5-pro supports only medium/high/xhigh) — pin to high.
        # CODEX_REASONING_EFFORT takes precedence when set.
        if [[ -n "$CODEX_REASONING_EFFORT" ]]; then
            CODEX_TOML+="model_reasoning_effort = \"$CODEX_REASONING_EFFORT\""$'\n'
        elif [[ "$MODEL" == *-pro* ]]; then
            CODEX_TOML+="model_reasoning_effort = \"high\""$'\n'
        fi
        if [[ -n "$CODEX_TOML" ]]; then
            printf '%s' "$CODEX_TOML" > "$CODEX_HOME_DIR/config.toml"
            chmod 666 "$CODEX_HOME_DIR/config.toml"
        fi
        RUN_ARGS+=(-v "$CODEX_HOME_DIR:/home/codex/.codex")
        # Disable RTK to prevent environment bias in experiments
        RTK_NOOP=$(mktemp)
        printf '#!/bin/sh\nexit 0\n' > "$RTK_NOOP"
        chmod 755 "$RTK_NOOP"
        RUN_ARGS+=(-v "$RTK_NOOP:/home/codex/.local/bin/rtk")
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

if [[ -n "$OUTPUT_FILE" ]]; then
    "${RUN_ARGS[@]}" | tee "$OUTPUT_FILE"
else
    exec "${RUN_ARGS[@]}"
fi
