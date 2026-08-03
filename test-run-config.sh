#!/usr/bin/env bash
#
# test-run-config.sh - Regression tests for the codex config.toml that run.sh
# generates. Runs against a stub container runtime, so no image or network is
# needed: the stub prints the argv it was handed, and the test reads the
# config.toml out of the host directory run.sh bind-mounts at ~/.codex.
#
# Usage: ./test-run-config.sh

set -uo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
STUB_DIR="$(mktemp -d)"
trap 'rm -rf "$STUB_DIR"' EXIT

# Stub runtime: echo argv so the test can recover the mounted config dir.
cat > "$STUB_DIR/podman" <<'STUB'
#!/usr/bin/env bash
printf '%s\n' "$@"
STUB
chmod 755 "$STUB_DIR/podman"

PASS=0
FAIL=0

# Run run.sh against the stub and print the generated config.toml.
#
# LLM_ENV_FILE points at a path that does not exist unless a caller overrides
# it, so the repo's real .env is never loaded here: without this the developer's
# actual gateway key would be written into every fixture config.toml below.
generated_config() {
    local argv config_dir
    argv="$(LLM_ENV_FILE="${LLM_ENV_FILE:-$STUB_DIR/absent.env}" \
        PATH="$STUB_DIR:$PATH" "$SCRIPT_DIR/run.sh" \
        --backend codex --model claude-opus-5 --runtime podman \
        --workspace "$STUB_DIR" -p "noop" 2>/dev/null)"
    config_dir="$(grep -o '^[^ ]*:/home/agent/.codex$' <<< "$argv" | cut -d: -f1)"
    [[ -n "$config_dir" ]] && cat "$config_dir/config.toml" 2>/dev/null
}

check() {
    local name="$1" expected="$2" actual="$3"
    if [[ "$actual" == "$expected" ]]; then
        printf '  ok   %s\n' "$name"
        PASS=$((PASS + 1))
    else
        printf '  FAIL %s\n       expected: %s\n       actual:   %s\n' \
            "$name" "$expected" "$actual"
        FAIL=$((FAIL + 1))
    fi
}

echo "=== codex config.toml generation ==="

# Regression: codex ships no metadata for models outside its own catalogue
# (Anthropic models on the compat surface). Its fallback output ceiling
# truncates long turns mid-stream, and the reconnect prefills the partial
# assistant message, which the Anthropic API rejects — failing the whole turn.
# Pinning the two metadata keys is what keeps such a run alive.
CONFIG="$(CODEX_MAX_OUTPUT_TOKENS=32000 CODEX_CONTEXT_WINDOW=200000 generated_config)"
check "model_max_output_tokens is emitted when set" \
    "model_max_output_tokens = 32000" \
    "$(grep '^model_max_output_tokens' <<< "$CONFIG")"
check "model_context_window is emitted when set" \
    "model_context_window = 200000" \
    "$(grep '^model_context_window' <<< "$CONFIG")"

# Both keys stay absent unless asked for, so every run recorded before this
# flag existed reproduces byte-identically.
CONFIG="$(generated_config)"
check "model_max_output_tokens is absent by default" \
    "" "$(grep '^model_max_output_tokens' <<< "$CONFIG")"
check "model_context_window is absent by default" \
    "" "$(grep '^model_context_window' <<< "$CONFIG")"

# The pre-existing effort knob must keep working alongside the new keys.
CONFIG="$(CODEX_REASONING_EFFORT=high CODEX_MAX_OUTPUT_TOKENS=32000 generated_config)"
check "reasoning effort survives alongside the metadata keys" \
    "model_reasoning_effort = \"high\"" \
    "$(grep '^model_reasoning_effort' <<< "$CONFIG")"

echo ""
echo "=== image selection ==="

# The argv the stub runtime saw, so the tests can assert which image ran.
generated_argv() {
    LLM_ENV_FILE="${LLM_ENV_FILE:-$STUB_DIR/absent.env}" \
    PATH="$STUB_DIR:$PATH" "$SCRIPT_DIR/run.sh" \
        --backend codex --model claude-opus-5 --runtime podman \
        --workspace "$STUB_DIR" -p "noop" 2>/dev/null
}

check "IMAGE_TAG selects a published tag by default" \
    "ghcr.io/latere-ai/sandbox-harness:v0.0.14" \
    "$(generated_argv | grep '^ghcr.io/latere-ai/sandbox-harness:')"
check "IMAGE_TAG is honoured" \
    "ghcr.io/latere-ai/sandbox-harness:v0.0.15" \
    "$(IMAGE_TAG=v0.0.15 generated_argv | grep '^ghcr.io/latere-ai/sandbox-harness:')"

# Experiments that need CLI versions no published tag ships run a locally built
# image (harness.Dockerfile). Without this override the registry path is
# hardcoded and such a pin is unreachable.
check "IMAGE overrides the whole reference" \
    "sandbox-harness:pinned-local" \
    "$(IMAGE=sandbox-harness:pinned-local IMAGE_TAG=v0.0.15 generated_argv | grep '^sandbox-harness:')"

echo ""
echo "=== dotenv loading ==="

# A fixture dotenv standing in for the repo's real .env. The comment and blank
# line are here because the loader must skip them rather than try to export
# them as variables.
cat > "$STUB_DIR/fixture.env" <<'DOTENV'
# gateway credentials

LLM_GW_BASE_URL=https://gw.fixture.test
LLM_GW_API_KEY=key-from-dotenv
DOTENV

dotenv_config() { LLM_ENV_FILE="$STUB_DIR/fixture.env" generated_config; }

CONFIG="$(env -u LLM_GW_BASE_URL -u LLM_GW_API_KEY bash -c \
    "$(declare -f generated_config dotenv_config); \
     SCRIPT_DIR='$SCRIPT_DIR' STUB_DIR='$STUB_DIR' dotenv_config")"
check "base URL is read from the dotenv file" \
    "openai_base_url = \"https://gw.fixture.test/v1\"" \
    "$(grep '^openai_base_url' <<< "$CONFIG")"
check "API key is read from the dotenv file" \
    "openai_api_key = \"key-from-dotenv\"" \
    "$(grep '^openai_api_key' <<< "$CONFIG")"

# A real shell value outranks the file, so one-off overrides keep working.
CONFIG="$(LLM_GW_API_KEY=key-from-env dotenv_config)"
check "a non-empty environment value overrides the dotenv file" \
    "openai_api_key = \"key-from-env\"" \
    "$(grep '^openai_api_key' <<< "$CONFIG")"

# Regression: the Makefile does `export LLM_GW_API_KEY ?=`, which exports the
# variable *set but empty*. An is-set guard would read that as a deliberate
# override and drop the dotenv value, leaving `make claude` with no credentials.
CONFIG="$(LLM_GW_API_KEY= dotenv_config)"
check "an empty exported value does not mask the dotenv file" \
    "openai_api_key = \"key-from-dotenv\"" \
    "$(grep '^openai_api_key' <<< "$CONFIG")"

# The loader must not be reachable by accident: an absent file is a no-op, not
# an error, so a fresh clone with no .env still runs.
CONFIG="$(env -u LLM_GW_BASE_URL -u LLM_GW_API_KEY bash -c \
    "$(declare -f generated_config); \
     SCRIPT_DIR='$SCRIPT_DIR' STUB_DIR='$STUB_DIR' \
     LLM_ENV_FILE='$STUB_DIR/absent.env' generated_config")"
check "a missing dotenv file leaves the gateway keys unset" \
    "" "$(grep -E '^openai_(base_url|api_key)' <<< "$CONFIG")"

echo ""
echo "Passed: $PASS  Failed: $FAIL"
[[ $FAIL -eq 0 ]]
