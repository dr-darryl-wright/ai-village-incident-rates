#!/usr/bin/env bash
# Hash the pilot protocol and everything it depends on; write pilot/FREEZE-<UTC>.txt with a combined hash.
set -euo pipefail; cd "$(dirname "$0")/.."
files=(pilot/PILOT_PROTOCOL.md pilot/scoring_prompt.md analysis/render.py analysis/08a_session_signals.py analysis/08b_build_pilot_inputs.py analysis/09_score_batch.py analysis/10_pilot_estimate.py outputs/session_signals.csv.gz)
t=$(date -u +%Y-%m-%dT%H%M%SZ); out="pilot/FREEZE-$t.txt"
{ echo "Pilot freeze $t (UTC)"; sha256sum "${files[@]}"; } > "$out"
echo "combined $(sha256sum "${files[@]}" | sha256sum | cut -d' ' -f1)" >> "$out"; cat "$out"
