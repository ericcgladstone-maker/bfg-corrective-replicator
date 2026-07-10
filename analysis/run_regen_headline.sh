#!/bin/bash
# Regenerate all older-code headline datasets under the CURRENT pinned code, into _v2
# folders, so the whole dataset shares one md5. Order: current-paper data first
# (run2, run1, extinction, slots, toy 4-peak), then exploratory (stage4, stage3).
# Resume-safe; run under caffeinate. Old folders are kept for the regression check.
set -uo pipefail
cd "$(dirname "$0")/.."
PY=python3

echo "=== run2 (close, headline) ==="
$PY analysis/run_stage2.py --peaks close --out data/stage2_run2_v2

echo "=== run1 (far) ==="
$PY analysis/run_stage2.py --peaks far --out data/stage2_run1_v2

echo "=== extinction preview (gen 250) ==="
$PY analysis/run_stage2.py --peaks close --extinction-gen 250 --scalars 0.5,1.0 \
   --vreapers top_fitness --reps 20 --out data/stage2_extinction_v2

echo "=== slots sweep ==="
$PY analysis/run_stage2.py --peaks close --scalars 0.5,1.0 --vreapers top_fitness \
   --reps 10 --slots 5,10,20,40 --out data/stage2_slots_v2

echo "=== toy 4-peak pruning test (Table 10) ==="
$PY analysis/run_stage2.py --peak-indices 0,13,16,36 --scalars 1.0 \
   --vreapers top_fitness,random --reps 20 --out data/stage2_toy4peak

echo "=== stage4 topology (exploratory) ==="
$PY analysis/run_stage4.py --out data/stage4_v2

echo "=== stage3 heritable (exploratory, 1000 gens, slowest last) ==="
$PY analysis/run_stage3.py --out data/stage3_v2

echo "=== REGEN COMPLETE ==="
