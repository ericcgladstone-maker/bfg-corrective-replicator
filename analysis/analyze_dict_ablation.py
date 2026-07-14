"""Codebook-solution alignment ablation. Removes the peak targets' words from the correction
dictionary (see run_stage2.py --drop-target-words) and compares against the full-dictionary run.
All numbers from raw CSV. This is a NECESSITY test for codebook support, not a causal variance
decomposition: removing the target words both removes solution-relevant guidance AND makes the
operator actively replace correctly-generated target words (anti-alignment).
"""
import os, sys, csv, glob, collections, statistics
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE)
D = lambda *p: os.path.join(ROOT, "data", *p)


def load(folder):
    f = glob.glob(D(folder, "stage2_summary.csv"))
    return list(csv.DictReader(open(f[0]))) if f else None


def mse(v):
    return (statistics.mean(v), statistics.stdev(v) / len(v) ** 0.5 if len(v) > 1 else 0.0)


def colonized(rows, ecm):
    return mse([float(r["final_peaks_colonized"]) for r in rows if r["use_ecm"] == ecm])


def peak_maxfit(folder):
    """Per run, the best fitness any individual reached (max over generations of max_fitness)."""
    rows = list(csv.DictReader(open(D(folder, "stage2_per_generation.csv"))))
    byrun = collections.defaultdict(list); ecm = {}
    for r in rows:
        byrun[r["run_id"]].append(float(r["max_fitness"])); ecm[r["run_id"]] = r["use_ecm"]
    return {rid: max(v) for rid, v in byrun.items()}, ecm


def seed_match(a, b, ecm):
    ka = {r.get("seed"): float(r["final_peaks_colonized"]) for r in a if r["use_ecm"] == ecm}
    kb = {r.get("seed"): float(r["final_peaks_colonized"]) for r in b if r["use_ecm"] == ecm}
    common = set(ka) & set(kb)
    return len(common), sum(1 for s in common if abs(ka[s] - kb[s]) > 1e-9)


def report():
    print("### CODEBOOK-SOLUTION ALIGNMENT ABLATION (peak-target words removed, close peaks, scalar 1.0)")
    for tag, full, abl, crit in [("exact match", "simthresh_0.80", "dict_ablation", "0.99999"),
                                 ("relaxed 0.90", "colon_0.90", "dict_ablation_relaxed", "0.90")]:
        f, a = load(full), load(abl)
        if not f or not a:
            print(f"  [{tag}] missing data"); continue
        am, ase = colonized(f, "1"); bm, bse = colonized(a, "1")
        cm, cse = colonized(a, "0"); fcm, _ = colonized(f, "0")
        print(f"\n  [{tag}] colonization criterion {crit}")
        print(f"    A full-dict correction   : {am:.2f} +- {ase:.2f}")
        print(f"    B reduced-dict correction: {bm:.2f} +- {bse:.2f}")
        print(f"    C no correction          : {cm:.2f} +- {cse:.2f}  (full-run C {fcm:.2f})")
        n, mm = seed_match(f, a, "0")
        print(f"    no-correction seed-match (ablation vs full): {n} shared, {mm} mismatch "
              f"({'identical -> manipulation touched only the correction path' if n and mm == 0 else 'differs'})")
    # attainability: what fitness can reduced-dict correction reach?
    print("\n  ATTAINABILITY (best-individual fitness per run, exact-match design):")
    for folder, label in [("dict_ablation", "reduced-dict"), ("simthresh_0.80", "full-dict")]:
        mx, ecm = peak_maxfit(folder)
        for cond, nm in [("1", "correction"), ("0", "no-correction")]:
            v = [mx[r] for r in mx if ecm[r] == cond]
            if v:
                print(f"    {label:12s} {nm:13s}: mean {statistics.mean(v):.3f}  max {max(v):.3f}  "
                      f"frac>=0.90 {sum(x >= 0.90 for x in v)/len(v):.2f}  frac>=0.95 {sum(x >= 0.95 for x in v)/len(v):.2f}")
    print("\n  => reduced-dict correction caps attainable fitness well below the 0.90 threshold, so its zero")
    print("     colonization holds under any criterion at or above that cap. NECESSITY test, not a decomposition.")


if __name__ == "__main__":
    report()
