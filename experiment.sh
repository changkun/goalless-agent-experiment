#!/usr/bin/env bash
#
# experiment.sh - Run backend × model combinations with the same prompt.
#
# All combinations within a single run execute in parallel. The script waits
# for every job to finish before starting the next run (if RUNS > 1).
#
# Usage:
#   ./experiment.sh [--runs N] [--backends claude,codex] [--models LIST|FILE]
#   ./experiment.sh --models models.txt --backends claude,codex --runs 5

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
RUNTIME="docker"
DRY_RUN="false"
RUNS=1
MAX_JOBS=0  # 0 = unlimited (all combos in parallel)
PROMPT_FILE=""
RESULTS_DIR=""
USER_MODELS=""
USER_BACKENDS=""
PARALLEL_RUNS="false"

# --- Known Claude models (for auto-backend detection) ---
CLAUDE_MODELS=(
    claude-sonnet-4.6
    claude-sonnet-4.5
    claude-opus-4.6
    claude-opus-4.5
    claude-haiku-4.5
)

ALL_MODELS=(
    "${CLAUDE_MODELS[@]}"
    vertex_ai/gemini-3-pro
    vertex_ai/gemini-3-flash
    vertex_ai/gemini-2.5-pro
    vertex_ai/gemini-2.5-flash
    vertex_ai/gemini-2.0-flash
    azure/gpt-4.1
    azure/gpt-4.1-mini
    azure/gpt-5.1
    azure/gpt-5
    azure/gpt-5-mini
    azure/gpt-5-nano
    azure/gpt-4o
    azure/gpt-4o-mini
)

usage() {
    cat <<'EOF'
Usage: ./experiment.sh [options]

Options:
  --runs       N          Number of runs per combination (default: 1)
  --jobs       N          Max concurrent jobs (default: 0 = unlimited)
  --parallel-runs         Do not serialize runs; flatten the whole
                          (combo x run) matrix into one pool. Requires --jobs.
                          Without it, runs execute one after another, so a
                          single-model matrix is fully serial.
  --models     LIST|FILE  Comma-separated models or path to file (default: all)
  --backends   LIST       Comma-separated backends: claude,codex (default: auto)
  --prompt     FILE       Prompt file (default: prompt.txt)
  --results-dir DIR       Output directory (default: results/)
  --runtime    NAME       docker or podman (default: docker)
  --dry-run               Print what would run without executing
  -h, --help              Show this help

All backend x model combinations within a run execute in parallel.
The script waits for every job before starting the next run, unless
--parallel-runs is given.
EOF
    exit 1
}

# --- Parse arguments ---
while [[ $# -gt 0 ]]; do
    case $1 in
        --runs)       RUNS="$2";         shift 2 ;;
        --jobs)       MAX_JOBS="$2";     shift 2 ;;
        --models)     USER_MODELS="$2";  shift 2 ;;
        --backends)   USER_BACKENDS="$2"; shift 2 ;;
        --prompt)     PROMPT_FILE="$2";  shift 2 ;;
        --results-dir) RESULTS_DIR="$2"; shift 2 ;;
        --runtime)    RUNTIME="$2";      shift 2 ;;
        --parallel-runs) PARALLEL_RUNS="true"; shift ;;
        --dry-run)    DRY_RUN="true";    shift   ;;
        -h|--help)    usage ;;
        *)            echo "Unknown option: $1" >&2; usage ;;
    esac
done

# Defaults
[[ -z "$PROMPT_FILE" ]] && PROMPT_FILE="$SCRIPT_DIR/prompt.txt"
[[ -z "$RESULTS_DIR" ]] && RESULTS_DIR="$SCRIPT_DIR/results"

if [[ "$PARALLEL_RUNS" == "true" && "$MAX_JOBS" -le 0 ]]; then
    echo "Error: --parallel-runs requires --jobs N (an unbounded pool would" >&2
    echo "       launch every run at once and exhaust the machine)" >&2
    exit 1
fi

if [[ ! -f "$PROMPT_FILE" ]]; then
    echo "Error: prompt file not found at $PROMPT_FILE" >&2
    exit 1
fi

PROMPT="$(cat "$PROMPT_FILE")"

# --- Resolve models ---
MODELS=()
if [[ -z "$USER_MODELS" ]]; then
    MODELS=("${ALL_MODELS[@]}")
elif [[ -f "$USER_MODELS" ]]; then
    while IFS= read -r line; do
        line="${line%%#*}"          # strip comments
        line="$(echo "$line" | xargs)" # trim whitespace
        [[ -n "$line" ]] && MODELS+=("$line")
    done < "$USER_MODELS"
else
    IFS=',' read -ra MODELS <<< "$USER_MODELS"
fi

# --- Resolve backends ---
is_claude_model() {
    [[ "$1" == anthropic/* || "$1" == claude-* ]] && return 0
    return 1
}

auto_backend() {
    if is_claude_model "$1"; then echo "claude"; else echo "codex"; fi
}

BACKENDS=()
if [[ -z "$USER_BACKENDS" || "$USER_BACKENDS" == "auto" ]]; then
    BACKENDS=("auto")
else
    IFS=',' read -ra BACKENDS <<< "$USER_BACKENDS"
fi

# --- Build the job matrix: (backend, model) pairs ---
MATRIX_BACKENDS=()
MATRIX_MODELS=()

for model in "${MODELS[@]}"; do
    if [[ "${BACKENDS[0]}" == "auto" ]]; then
        b="$(auto_backend "$model")"
        MATRIX_BACKENDS+=("$b")
        MATRIX_MODELS+=("$model")
    else
        for b in "${BACKENDS[@]}"; do
            MATRIX_BACKENDS+=("$b")
            MATRIX_MODELS+=("$model")
        done
    fi
done

COMBOS=${#MATRIX_BACKENDS[@]}
TOTAL_JOBS=$((COMBOS * RUNS))

# Folder name: strip provider prefix
folder_name() { echo "$1" | sed 's|^[^/]*/||'; }

echo "=== Experiment ==="
echo "Prompt:      $(head -1 <<< "$PROMPT")..."
echo "Models:      ${#MODELS[@]}"
echo "Backends:    ${BACKENDS[*]}"
echo "Combos:      $COMBOS"
echo "Runs/combo:  $RUNS"
echo "Total jobs:  $TOTAL_JOBS"
if [[ "$MAX_JOBS" -gt 0 ]]; then
    echo "Parallel:    max $MAX_JOBS concurrent"
else
    echo "Parallel:    yes (all combos per run)"
fi
echo "Runtime:     $RUNTIME"
echo "Results:     $RESULTS_DIR"
echo ""

# --- Per-job state (written by subshells, read after wait) ---
JOBS_DIR=$(mktemp -d)
trap 'rm -rf "$JOBS_DIR"' EXIT

run_one() {
    local backend="$1"
    local model="$2"
    local run_num="$3"
    local job_id="$4"
    local folder
    folder="$(folder_name "$model")"
    local run_dir="$RESULTS_DIR/$backend/$folder/run-$(printf '%02d' "$run_num")"

    mkdir -p "$run_dir/workspace"
    chmod 777 "$run_dir/workspace"

    if [[ "$DRY_RUN" == "true" ]]; then
        echo "  [dry-run] $backend / $model / run-$run_num"
        echo "0" > "$JOBS_DIR/$job_id.exit"
        return
    fi

    local start_time end_time duration exit_code
    start_time=$(date +%s)

    set +e
    "$SCRIPT_DIR/run.sh" \
        --backend "$backend" \
        --model "$model" \
        --workspace "$run_dir/workspace" \
        --runtime "$RUNTIME" \
        --batch \
        --transcript "$run_dir/transcript.jsonl" \
        -p "$PROMPT" \
        > "$run_dir/output.json" \
        2> "$run_dir/log.txt"
    exit_code=$?
    set -e

    end_time=$(date +%s)
    duration=$((end_time - start_time))

    # Write metadata
    cat > "$run_dir/meta.md" <<METAEOF
# Run Metadata

| Field | Value |
|-------|-------|
| Backend | $backend |
| Model | $model |
| Run | $run_num |
| Exit Code | $exit_code |
| Duration | ${duration}s |
| Timestamp | $(date -u +%Y-%m-%dT%H:%M:%SZ) |

## Prompt

$PROMPT
METAEOF

    # Write job result for summary
    echo "$exit_code" > "$JOBS_DIR/$job_id.exit"
    echo "$duration"  > "$JOBS_DIR/$job_id.duration"
    echo "$run_dir"   > "$JOBS_DIR/$job_id.dir"

    local status="OK"
    [[ $exit_code -ne 0 ]] && status="FAIL"
    printf "  %-4s %4ss  %-6s %-35s run-%02d → %s\n" \
        "$status" "$duration" "$backend" "$model" "$run_num" "$run_dir"
}

# --- Run all combinations in parallel per run ---
PASSED=0
FAILED=0
FAILED_LIST=()

# Wait until fewer than MAX_JOBS background jobs are running.
throttle() {
    if [[ "$MAX_JOBS" -gt 0 ]]; then
        while [[ $(jobs -rp | wc -l) -ge "$MAX_JOBS" ]]; do
            sleep 1
        done
    fi
}

# --parallel-runs flattens the whole (combo × run) matrix into one throttled
# pool, so a single-model experiment can still saturate the machine — by
# default the barrier is per run, which serializes a 1-combo matrix completely.
#
# This is opt-in, and requires --jobs, for two reasons: every experiment
# recorded before the flag reproduces its original scheduling untouched, and an
# unbounded pool would launch every run at once (Exp12 already lost a run to
# OOM at far lower concurrency).
if [[ "$PARALLEL_RUNS" == "true" ]]; then
    echo "--- All $TOTAL_JOBS jobs, max $MAX_JOBS parallel (runs not serialized) ---"
    PIDS=()
    ALL_JOB_IDS=()

    for ((r = 1; r <= RUNS; r++)); do
        for ((i = 0; i < COMBOS; i++)); do
            backend="${MATRIX_BACKENDS[$i]}"
            model="${MATRIX_MODELS[$i]}"
            job_id="${backend}_$(folder_name "$model")_run${r}"
            throttle
            run_one "$backend" "$model" "$r" "$job_id" &
            PIDS+=($!)
            ALL_JOB_IDS+=("$job_id")
        done
    done

    for pid in "${PIDS[@]}"; do
        wait "$pid" 2>/dev/null || true
    done

    for job_id in "${ALL_JOB_IDS[@]}"; do
        exit_file="$JOBS_DIR/$job_id.exit"
        if [[ -f "$exit_file" ]] && [[ "$(cat "$exit_file")" -eq 0 ]]; then
            PASSED=$((PASSED + 1))
        else
            FAILED=$((FAILED + 1))
            FAILED_LIST+=("$job_id")
        fi
    done

    echo ""
    echo "=== Summary ==="
    echo "Total: $TOTAL_JOBS  Passed: $PASSED  Failed: $FAILED"
    if [[ ${#FAILED_LIST[@]} -gt 0 ]]; then
        echo "Failed runs:"
        for f in "${FAILED_LIST[@]}"; do
            echo "  - $f"
        done
    fi
    echo "Results in: $RESULTS_DIR"
    exit 0
fi

for ((r = 1; r <= RUNS; r++)); do
    local_label="all"
    [[ "$MAX_JOBS" -gt 0 ]] && local_label="max $MAX_JOBS"
    echo "--- Run $r/$RUNS ($COMBOS jobs, $local_label parallel) ---"
    PIDS=()
    JOB_IDS=()

    for ((i = 0; i < COMBOS; i++)); do
        backend="${MATRIX_BACKENDS[$i]}"
        model="${MATRIX_MODELS[$i]}"
        job_id="${backend}_$(folder_name "$model")_run${r}"

        # Throttle: if MAX_JOBS > 0, wait until a slot is free
        throttle

        run_one "$backend" "$model" "$r" "$job_id" &
        PIDS+=($!)
        JOB_IDS+=("$job_id")
    done

    # Wait for all jobs in this run
    for pid in "${PIDS[@]}"; do
        wait "$pid" 2>/dev/null || true
    done

    # Collect results
    for job_id in "${JOB_IDS[@]}"; do
        exit_file="$JOBS_DIR/$job_id.exit"
        if [[ -f "$exit_file" ]] && [[ "$(cat "$exit_file")" -eq 0 ]]; then
            PASSED=$((PASSED + 1))
        else
            FAILED=$((FAILED + 1))
            FAILED_LIST+=("$job_id")
        fi
    done

    echo ""
done

# --- Summary ---
echo "=== Summary ==="
echo "Total: $TOTAL_JOBS  Passed: $PASSED  Failed: $FAILED"
if [[ ${#FAILED_LIST[@]} -gt 0 ]]; then
    echo "Failed runs:"
    for f in "${FAILED_LIST[@]}"; do
        echo "  - $f"
    done
fi
echo "Results in: $RESULTS_DIR"
