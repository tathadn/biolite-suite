#!/bin/bash
# Judge wrapper: runs llm_judge.py for all five prediction sets in series.
# Sonnet judge throughout (matches everything else in the pipeline).
# Sonnet-judging-Sonnet is acknowledged self-eval bias; Opus scores under the
# same judge serve as the bias-independent reference point.
set -euo pipefail

ROOT="/fs1/scratch/tathadbn/biolite-suite"
INTERPRET="$ROOT/biolite-interpret/evaluation"
METHODS="$ROOT/biolite-methods/evaluation"

run_judge() {
    local label=$1 preds=$2 rubric=$3 out=$4
    if [[ ! -f "$preds" ]]; then
        echo "SKIP $label (no predictions: $preds)"
        return 0
    fi
    if [[ -f "$out" ]]; then
        echo "SKIP $label (already judged: $out)"
        return 0
    fi
    echo "[$label] judging $preds -> $out"
    python3 "$INTERPRET/llm_judge.py" \
        --predictions "$preds" \
        --rubric "$rubric" \
        --output "$out" \
        --model sonnet \
        --delay 2.0
}

run_judge "claude-sonnet phase1" \
    "$INTERPRET/results/predictions_claude_sonnet.json" \
    interpret \
    "$INTERPRET/results/judge_claude_sonnet.json"

run_judge "claude-sonnet phase2" \
    "$METHODS/results/predictions_claude_sonnet.json" \
    methods \
    "$METHODS/results/judge_claude_sonnet.json"

run_judge "claude-opus phase1" \
    "$INTERPRET/results/predictions_claude_opus.json" \
    interpret \
    "$INTERPRET/results/judge_claude_opus.json"

run_judge "claude-opus phase2" \
    "$METHODS/results/predictions_claude_opus.json" \
    methods \
    "$METHODS/results/judge_claude_opus.json"

run_judge "3b-fewshot phase1" \
    "$INTERPRET/results/predictions_3b_fewshot.json" \
    interpret \
    "$INTERPRET/results/judge_3b_fewshot.json"

echo "All judging complete."
