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
generated_config() {
    local argv config_dir
    argv="$(PATH="$STUB_DIR:$PATH" "$SCRIPT_DIR/run.sh" \
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
echo "Passed: $PASS  Failed: $FAIL"
[[ $FAIL -eq 0 ]]
