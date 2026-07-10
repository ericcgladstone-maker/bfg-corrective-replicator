#!/bin/bash
# Ease-asymmetry / reaper gradient: run the RANDOM valley reaper across the 6 distance-
# ladder peak sets (top_fitness already exists there), scalars 0.5+1.0, 20 reps, ECM on/off.
# Appends into the same data/stage2_distance/mpw* folders (run_id includes reaper).
set -uo pipefail
cd "$(dirname "$0")/.."
declare -a SETS=("46 0,13,16,36,84" "52 0,10,19,39,48" "57 0,28,49,61,76" "62 0,24,34,43,79" "67 0,46,53,55,62" "72 0,29,53,77,93")
for row in "${SETS[@]}"; do
  mpw="${row%% *}"; idx="${row#* }"
  echo "=== reaper=random mpw=$mpw peaks=$idx ==="
  python3 analysis/run_stage2.py --peak-indices "$idx" --scalars 0.5,1.0 --reps 20 \
     --vreapers random --slots 10 --out "data/stage2_distance/mpw${mpw}"
done
echo "=== REAPER GRADIENT DONE ==="
