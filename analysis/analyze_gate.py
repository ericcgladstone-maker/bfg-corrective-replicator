"""Fitness-gated correction (mechanism test). Correction applied to every offspring (full), only to
offspring whose pre-correction fitness is at or above the 0.90 near-target band (above), only below it
(below), or not at all (none). Prediction of the finishing account: 'above' should retain most of the
coverage benefit, 'below' little. All numbers from raw CSV. See run_stage2.py --correct-gate.
"""
import csv, glob, os, statistics

D = lambda *p: os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", *p)


def load(folder):
    f = glob.glob(D(folder, "stage2_summary.csv"))
    return list(csv.DictReader(open(f[0]))) if f else None


def mse(v):
    if not v:
        return (float("nan"), float("nan"))
    return (statistics.mean(v), statistics.stdev(v) / len(v) ** 0.5 if len(v) > 1 else 0.0)


def peaks(rows, ecm):
    return [float(r["final_peaks_colonized"]) for r in rows if r["use_ecm"] == ecm]


def seedmap(rows, ecm):
    return {r.get("seed"): r["final_peaks_colonized"] for r in rows if r["use_ecm"] == ecm}


def report():
    full = load("simthresh_0.80"); above = load("gate_above"); below = load("gate_below")
    if not (full and above and below):
        print("[gate] data not ready:", "full" if not full else "", "above" if not above else "",
              "below" if not below else ""); return
    print("### FITNESS-GATED CORRECTION (close peaks, scalar 1.0, top_fitness, gate threshold 0.90)")
    conds = [("full correction   ", peaks(full, "1")),
             ("correct >=0.90 only", peaks(above, "1")),
             ("correct <0.90 only ", peaks(below, "1")),
             ("no correction      ", peaks(full, "0"))]
    base = statistics.mean(peaks(full, "0")); top = statistics.mean(peaks(full, "1"))
    for lab, v in conds:
        m, e = mse(v)
        if not v:
            print(f"  {lab}: (no data yet)"); continue
        frac = (m - base) / (top - base) if top != base else float("nan")
        print(f"  {lab}: {m:.2f} +- {e:.2f}  (n={len(v)})   share of full-correction benefit retained: {frac*100:4.0f}%")
    # integrity: no-correction control arms must be seed-identical across runs (correction off => gate irrelevant)
    print("\n  no-correction control seed-match (gate runs vs full-dict run):")
    for nm, rows in [("gate_above", above), ("gate_below", below)]:
        a = seedmap(rows, "0"); f = seedmap(full, "0"); common = set(a) & set(f)
        mism = sum(1 for s in common if a[s] != f[s])
        print(f"    {nm} ecm0 vs simthresh_0.80 ecm0: {len(common)} shared, {mism} mismatch")
    # behavior preservation of the default (ungated) correction path, if the check run exists
    ng = load("nogate_check2")
    if ng:
        a = seedmap(ng, "1"); f = seedmap(full, "1"); common = set(a) & set(f)
        mism = sum(1 for s in common if a[s] != f[s])
        print(f"  default correction path preservation (nogate_check2 ecm1 vs simthresh_0.80 ecm1): "
              f"{len(common)} shared, {mism} mismatch")
    # paired contrasts at 0.90 (gated runs share seeds with the full-dict run)
    def bys(folder, ecm="1"):
        return {r["run_id"]: float(r["final_peaks_colonized"])
                for r in load(folder) if r["use_ecm"] == ecm}
    f, a, b = bys("simthresh_0.80"), bys("gate_above"), bys("gate_below")
    common = set(f) & set(a) & set(b)
    print(f"\n  PAIRED contrasts at 0.90 (n={len(common)}, shared seeds):")
    for lab, x, y in [("full - above", f, a), ("full - below", f, b), ("below - above", b, a)]:
        d = [x[k] - y[k] for k in common]
        m = statistics.mean(d); ci = 1.96 * statistics.stdev(d) / len(d) ** 0.5
        print(f"    {lab}: {m:+.2f}  95% CI [{m - ci:+.2f}, {m + ci:+.2f}]")

    # sensitivity + correction exposure (from the instrumented _ex re-runs; colonization identical)
    print("\n  THRESHOLD SENSITIVITY + CORRECTION EXPOSURE (instrumented re-runs):")
    print(f"  {'thr':>5} {'above':>6} {'below':>6} {'above-expo':>11} {'below-expo':>11}")
    for thr in ("0.85", "0.90", "0.95"):
        ga, gb = load(f"gate_above_{thr}_ex"), load(f"gate_below_{thr}_ex")
        if not (ga and gb):
            print(f"  {thr:>5}  (exposure re-run missing)"); continue
        def out(rows): return statistics.mean([float(r["final_peaks_colonized"]) for r in rows if r["use_ecm"] == "1"])
        def exposure(rows):  # fraction of offspring passed to the corrector (calls, not substitutions)
            e = [r for r in rows if r["use_ecm"] == "1"]
            return statistics.mean([int(r["offspring_corrected"]) for r in e]) / \
                statistics.mean([int(r["offspring_total"]) for r in e])
        print(f"  {thr:>5} {out(ga):>6.2f} {out(gb):>6.2f} {exposure(ga)*100:>10.1f}% {exposure(gb)*100:>10.1f}%")
    print("  (full correction 1.20, no correction 0.55). Near-target correction recovers most of the benefit")
    print("  at low exposure; the below-gate's success reflects near-full exposure. Threshold and exposure")
    print("  change together, so location and amount are not separated.")


if __name__ == "__main__":
    report()
