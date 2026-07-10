#!/bin/bash
# July 9 sweeps: inter-peak distance (Sweep 3) + extinction-timing (Sweep 2).
# All runs use the CURRENT bfg_stage2.py (do not mix with older-code data).
# Resume-safe: re-running skips completed run_ids. Run under caffeinate.
set -euo pipefail
cd "$(dirname "$0")/.."   # project root
PY=python3
H=analysis/run_stage2.py
COMMON="--scalars 0.5 --reps 20 --vreapers top_fitness --slots 10"

echo "=== SWEEP 3b: distance, scalar 0.5 (pool) ==="
# mean pairwise Levenshtein: 46 52 57 62 67 72
declare -a SETS=(
  "46 0,13,16,36,84"
  "52 0,10,19,39,48"
  "57 0,28,49,61,76"
  "62 0,24,34,43,79"
  "67 0,46,53,55,62"
  "72 0,29,53,77,93"
)
for row in "${SETS[@]}"; do
  mpw="${row%% *}"; idx="${row#* }"
  echo ">>> distance mpw=$mpw peaks=$idx"
  $PY $H $COMMON --peak-indices "$idx" --out "data/stage2_distance/mpw${mpw}"
done

echo "=== SWEEP 2b: extinction-timing, scalar 0.5 (pool) ==="
for G in 150 200 250 300 350; do
  MAXG=$(( G + 250 ))
  echo ">>> extinction gen=$G max_gens=$MAXG"
  $PY $H $COMMON --peaks close --extinction-gen "$G" --max-gens "$MAXG" \
     --out "data/stage2_ext_timing/gen${G}"
done

echo "=== ALL SWEEPS DONE ==="
