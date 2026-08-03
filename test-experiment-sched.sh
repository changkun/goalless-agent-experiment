#!/usr/bin/env bash
#
# test-experiment-sched.sh - Regression tests for experiment.sh scheduling.
#
# experiment.sh invokes "$SCRIPT_DIR/run.sh", where SCRIPT_DIR is its own
# directory — so copying it into a temp dir beside a stub run.sh gives a real
# end-to-end scheduling test with no containers, no image, and no network.
#
# Usage: ./test-experiment-sched.sh

set -uo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
T="$(mktemp -d)"
trap 'rm -rf "$T"' EXIT

cp "$SCRIPT_DIR/experiment.sh" "$T/experiment.sh"
printf 'do something\n' > "$T/prompt.txt"

# Stub run.sh: brackets its lifetime in a shared log so the test can
# reconstruct how many ran at once.
cat > "$T/run.sh" <<'STUB'
#!/usr/bin/env bash
echo "START" >> "$SCHED_LOG"
sleep 1
echo "END" >> "$SCHED_LOG"
STUB
chmod 755 "$T/run.sh"

PASS=0
FAIL=0
check() {
    local name="$1" expected="$2" actual="$3"
    if [[ "$actual" == "$expected" ]]; then
        printf '  ok   %s\n' "$name"; PASS=$((PASS + 1))
    else
        printf '  FAIL %s\n       expected: %s\n       actual:   %s\n' \
            "$name" "$expected" "$actual"; FAIL=$((FAIL + 1))
    fi
}

# Highest number of stub runs alive at the same moment.
peak_concurrency() {
    awk '/START/{n++; if(n>m) m=n} /END/{n--} END{print m+0}' "$1"
}

echo "=== experiment.sh scheduling ==="

# The guard: an unbounded flattened pool would launch every run at once.
OUT="$("$T/experiment.sh" --models "m/x" --backends codex --runs 3 \
        --parallel-runs --prompt "$T/prompt.txt" --results-dir "$T/r0" 2>&1)"
RC=$?
check "--parallel-runs without --jobs is rejected" "1" "$RC"
check "...with an explanatory message" "yes" \
    "$(grep -q 'requires --jobs' <<< "$OUT" && echo yes || echo no)"

# Default scheduling is unchanged: runs are serialized behind a barrier, so a
# 1-combo matrix never has two runs in flight. This is what every experiment
# recorded before the flag relied on.
SCHED_LOG="$T/serial.log"; : > "$SCHED_LOG"
SCHED_LOG="$SCHED_LOG" "$T/experiment.sh" --models "m/x" --backends codex --runs 4 \
    --prompt "$T/prompt.txt" --results-dir "$T/r1" >/dev/null 2>&1
check "default: a single-model matrix stays serial" "1" \
    "$(peak_concurrency "$T/serial.log")"
check "default: every run still executes" "4" \
    "$(grep -c START "$T/serial.log")"

# --parallel-runs lifts the barrier so the same matrix saturates the pool.
SCHED_LOG="$T/par.log"; : > "$SCHED_LOG"
SCHED_LOG="$SCHED_LOG" "$T/experiment.sh" --models "m/x" --backends codex --runs 6 \
    --parallel-runs --jobs 3 --prompt "$T/prompt.txt" --results-dir "$T/r2" >/dev/null 2>&1
check "--parallel-runs: runs overlap" "yes" \
    "$([[ "$(peak_concurrency "$T/par.log")" -gt 1 ]] && echo yes || echo no)"
check "--parallel-runs: every run still executes" "6" \
    "$(grep -c START "$T/par.log")"

# The cap is a cap. Exceeding it is how a 150-run experiment OOMs the VM.
PEAK="$(peak_concurrency "$T/par.log")"
check "--parallel-runs: concurrency never exceeds --jobs" "yes" \
    "$([[ "$PEAK" -le 3 ]] && echo yes || echo no)"

echo ""
echo "Passed: $PASS  Failed: $FAIL  (peak concurrency observed: $PEAK)"
[[ $FAIL -eq 0 ]]
