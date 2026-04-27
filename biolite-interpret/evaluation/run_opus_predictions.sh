#!/bin/bash
# Launches Opus predictions for Phase 1 + Phase 2 in parallel as background jobs.
# Call this AFTER Sonnet predictions + Sonnet judging are complete.
# Each job writes to its own log; check those for progress.

set -euo pipefail
ROOT="/fs1/scratch/tathadbn/biolite-suite"
SCRIPT="$ROOT/biolite-interpret/evaluation/generate_claude_predictions.py"

cd "$ROOT/biolite-interpret/evaluation"
nohup python3 "$SCRIPT" \
    --test_file ../data/splits/test.json \
    --pinned_indices pinned_64_indices.json \
    --phase interpret \
    --output results/predictions_claude_opus.json \
    --model opus \
    --model_name claude-opus \
    --delay 1.5 \
    > "$ROOT/gen_claude_opus_phase1.log" 2>&1 &
PID1=$!
echo "Phase 1 (interpret, opus): pid=$PID1 log=$ROOT/gen_claude_opus_phase1.log"

cd "$ROOT/biolite-methods/evaluation"
nohup python3 "$SCRIPT" \
    --test_file ../data/splits/test.json \
    --phase methods \
    --output results/predictions_claude_opus.json \
    --model opus \
    --model_name claude-opus \
    --delay 1.5 \
    > "$ROOT/gen_claude_opus_phase2.log" 2>&1 &
PID2=$!
echo "Phase 2 (methods, opus):   pid=$PID2 log=$ROOT/gen_claude_opus_phase2.log"

echo "Both Opus jobs running in background. Monitor with:"
echo "  tail -f $ROOT/gen_claude_opus_phase{1,2}.log"
echo "Wait with:"
echo "  wait $PID1 $PID2"
