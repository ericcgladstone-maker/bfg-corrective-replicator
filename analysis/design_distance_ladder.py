"""Design the inter-peak distance ladder for Sweep 3.

Anchor on target 0 (the easiest/most-reachable peak, as in the 'close' design).
Sort the other targets by Levenshtein distance from the anchor, then build a
monotone family of 5-peak sets by taking companions at rank step s: companions =
nbr[step], nbr[2*step], nbr[3*step], nbr[4*step]. step=1 is the Run 2 'close'
cluster; larger step spreads the peaks out. For each set we report the actual
MEAN PAIRWISE Levenshtein distance, which is the x-axis of the sweep.

This is a design/inspection script only: it prints candidate sets so we can lock
the ladder. No simulation runs here.
"""
import os, sys, itertools
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import bfg_stage2 as s2
import run_stage2 as r2

word_set, tg_idx, seeds, targets = r2.load_real_data()
N = len(targets)
lev = s2.levenshtein


def mean_pairwise(idx):
    ds = [lev(targets[a], targets[b]) for a, b in itertools.combinations(idx, 2)]
    return sum(ds) / len(ds)


def mean_to_anchor(idx, anchor=0):
    ds = [lev(targets[anchor], targets[i]) for i in idx if i != anchor]
    return sum(ds) / len(ds)


# Reference sets from the existing runs
close_ref = r2.select_peaks_close(targets, 5)   # Run 2
far_ref = r2.select_peaks(targets, 5)           # Run 1
print(f"targets: {N}, lengths min/max {min(len(t) for t in targets)}/{max(len(t) for t in targets)}")
print(f"Run2 CLOSE {close_ref}  mean_pairwise={mean_pairwise(close_ref):.1f}  mean_to_anchor={mean_to_anchor(close_ref):.1f}")
print(f"Run1 FAR   {far_ref}  mean_pairwise={mean_pairwise(far_ref):.1f}  mean_to_anchor={mean_to_anchor(far_ref):.1f}")
print()

anchor = 0
# Seeded random search over 5-subsets that include the anchor, binned by mean
# pairwise distance so we can pick sets spanning close (46) -> far (72). Seeded =
# fully reproducible; the chosen indices get hard-coded + recorded in the manifest.
import random
random.seed(20260709)
others = [i for i in range(N) if i != anchor]
pool = {}  # rounded mean_pairwise -> (exact_mpw, idx)
for _ in range(200000):
    comp = random.sample(others, 4)
    idx = tuple(sorted([anchor] + comp))
    m = mean_pairwise(idx)
    key = round(m)
    if key not in pool or abs(m - key) < abs(pool[key][0] - key):
        pool[key] = (m, idx)

# Endpoints reuse existing runs; pick 4 intermediate targets between them.
targets_mpw = [52, 57, 62, 67]
print("Chosen ladder (endpoints = existing Run2/Run1 data; 4 intermediate to run):")
print(f"{'level':>7} {'target':>6} {'mean_pairwise':>13} {'mean_to_anchor':>14}  peak_indices")
print(f"{'close':>7} {'--':>6} {mean_pairwise(close_ref):>13.1f} {mean_to_anchor(close_ref):>14.1f}  {close_ref}  [REUSE run2_fixed]")
for t in targets_mpw:
    # nearest available bin to target
    best = min(pool.values(), key=lambda v: abs(v[0] - t))
    idx = list(best[1])
    print(f"{'mid':>7} {t:>6} {mean_pairwise(idx):>13.1f} {mean_to_anchor(idx):>14.1f}  {idx}")
print(f"{'far':>7} {'--':>6} {mean_pairwise(far_ref):>13.1f} {mean_to_anchor(far_ref):>14.1f}  {far_ref}  [REUSE run1]")
