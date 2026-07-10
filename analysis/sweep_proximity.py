"""Sweep 1: proximity-threshold (the 'finisher' / last-mile effect).

Re-analysis ONLY of existing data/stage2_run2_fixed per-generation CSVs. No new
simulation. For each proximity threshold T, among runs whose best string ever got
'close' to a peak (max_fitness >= T at some generation), what fraction went on to
reach an EXACT match (peaks_colonized >= 1), split by ECM on/off, plus the median
close->exact climb time in generations.

Faithful to the published last-mile method (docs/BFG_Dev_Log.md): at T=0.90 this
must reproduce 119/160 (ECM) and 57/137 (no-ECM). We assert that as a guard.

All numbers are computed from the raw CSV; nothing is hard-coded except the guard.
"""
import csv, os, statistics, collections, sys

HERE = os.path.dirname(os.path.abspath(__file__))
PROJECT = os.path.dirname(HERE)
PERGEN = os.path.join(PROJECT, "data", "stage2_run2_fixed", "stage2_per_generation.csv")

THRESHOLDS = [0.70, 0.75, 0.80, 0.85, 0.90]


def load_runs(path):
    """Group per-generation rows by run_id. Return dict run_id -> list of (gen, max_fit, peaks)."""
    runs = collections.defaultdict(list)
    meta = {}
    with open(path) as f:
        for r in csv.DictReader(f):
            rid = r["run_id"]
            runs[rid].append((int(r["generation"]),
                              float(r["max_fitness"]),
                              int(r["peaks_colonized"])))
            meta[rid] = int(r["use_ecm"])
    for rid in runs:
        runs[rid].sort(key=lambda x: x[0])
    return runs, meta


def analyze(runs, meta, T):
    """For threshold T, per ECM condition: (#got_close, #reached_exact, climb_gens list)."""
    out = {0: {"close": 0, "exact": 0, "climb": []},
           1: {"close": 0, "exact": 0, "climb": []}}
    for rid, series in runs.items():
        ecm = meta[rid]
        gen_close = None
        gen_exact = None
        for gen, mx, peaks in series:
            if gen_close is None and mx >= T:
                gen_close = gen
            if gen_exact is None and peaks >= 1:
                gen_exact = gen
        if gen_close is None:
            continue  # never got close at this threshold
        out[ecm]["close"] += 1
        if gen_exact is not None and gen_exact >= gen_close:
            out[ecm]["exact"] += 1
            out[ecm]["climb"].append(gen_exact - gen_close)
    return out


def main():
    if not os.path.exists(PERGEN):
        sys.exit(f"missing {PERGEN}")
    runs, meta = load_runs(PERGEN)
    print(f"loaded {len(runs)} runs from {os.path.relpath(PERGEN, PROJECT)}")
    n_ecm = sum(1 for v in meta.values() if v == 1)
    print(f"  ECM runs: {n_ecm}   no-ECM runs: {len(meta) - n_ecm}\n")

    # Guard: T=0.90 must reproduce the published denominators/numerators.
    g = analyze(runs, meta, 0.90)
    guard = (g[1]["exact"], g[1]["close"], g[0]["exact"], g[0]["close"])
    print(f"GUARD @0.90  ECM {g[1]['exact']}/{g[1]['close']}  noECM {g[0]['exact']}/{g[0]['close']}"
          f"  (published: ECM 119/160, noECM 57/137)")
    assert guard == (119, 160, 57, 137), f"last-mile method mismatch: {guard}"
    print("  guard OK -- method reproduces published last-mile result\n")

    print(f"{'T':>5} | {'ECM close':>9} {'ECM exact':>9} {'ECM %':>6} {'ECMclimb':>8} "
          f"| {'no close':>8} {'no exact':>8} {'no %':>6} {'noclimb':>8}")
    rows = []
    for T in THRESHOLDS:
        a = analyze(runs, meta, T)
        e, n = a[1], a[0]
        ep = 100 * e["exact"] / e["close"] if e["close"] else float("nan")
        np_ = 100 * n["exact"] / n["close"] if n["close"] else float("nan")
        emed = statistics.median(e["climb"]) if e["climb"] else float("nan")
        nmed = statistics.median(n["climb"]) if n["climb"] else float("nan")
        print(f"{T:>5.2f} | {e['close']:>9} {e['exact']:>9} {ep:>5.0f}% {emed:>8.0f} "
              f"| {n['close']:>8} {n['exact']:>8} {np_:>5.0f}% {nmed:>8.0f}")
        rows.append({"T": T, "ecm_close": e["close"], "ecm_exact": e["exact"], "ecm_pct": ep,
                     "ecm_climb": emed, "no_close": n["close"], "no_exact": n["exact"],
                     "no_pct": np_, "no_climb": nmed})
    return rows


if __name__ == "__main__":
    main()
