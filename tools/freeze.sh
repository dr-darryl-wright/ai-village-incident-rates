#!/usr/bin/env bash
# Hash the pilot protocol and everything it depends on; write pilot/FREEZE-<UTC>.txt with a combined hash.
# First checks that the scorer's prompt is exactly the annotated copy with markers and the CLTR paragraph removed.
set -euo pipefail; cd "$(dirname "$0")/.."
python3 tools/make_scorer_prompt.py --check
files=(pilot/PILOT_PROTOCOL.md pilot/scoring_prompt_annotated.md pilot/scoring_prompt.md tools/make_scorer_prompt.py analysis/render.py analysis/08a_session_signals.py analysis/08b_build_pilot_inputs.py analysis/08c_prefreeze_checks.py analysis/09_score_batch.py analysis/10_pilot_estimate.py outputs/session_signals.csv.gz outputs/prefreeze_checks.txt outputs/prefreeze_checks_original_patterns.txt)
t=$(date -u +%Y-%m-%dT%H%M%SZ); out="pilot/FREEZE-$t.txt"
{ echo "Pilot freeze $t (UTC)"; sha256sum "${files[@]}"; } > "$out"
echo "combined $(sha256sum "${files[@]}" | sha256sum | cut -d' ' -f1)" >> "$out"; cat "$out"
