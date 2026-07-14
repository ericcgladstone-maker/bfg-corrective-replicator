"""Analyze the July 12 reviewer-driven robustness runs. Each block runs only if its data
exists, so this can be run partially. All values from raw CSV. Figures in figures/pub/.
"""
import os, sys, csv, glob, json, statistics, collections
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
ROOT = os.path.dirname(HERE)
D = lambda *p: os.path.join(ROOT, "data", *p)
E = lambda r: r["use_ecm"] == "1"; N = lambda r: r["use_ecm"] == "0"
def mse(v): return (statistics.mean(v), statistics.stdev(v)/len(v)**0.5 if len(v) > 1 else 0.0)
def load(folder):
    f = glob.glob(D(folder, "*summary*.csv")); return list(csv.DictReader(open(f[0]))) if f else None

try:
    import pubfig, matplotlib.pyplot as plt
    pubfig.apply(); COL = pubfig.COL; HAVE_PLT = True
except Exception:
    HAVE_PLT = False
OUT = os.path.join(ROOT, "figures", "pub")


def asymptotic():
    pg = D("asymptotic", "stage2_per_generation.csv")
    if not os.path.exists(pg): return print("[asymptotic] no data yet")
    byrun = collections.defaultdict(dict); ecm = {}
    for r in csv.DictReader(open(pg)):
        byrun[r["run_id"]][int(r["generation"])] = int(r["peaks_colonized"]); ecm[r["run_id"]] = r["use_ecm"]
    gmax = max(max(v) for v in byrun.values())
    # peaks_colonized is CUMULATIVE (a peak, once colonized, stays counted). Runs that stop early
    # (blanket / no-progress patience) have no rows past their last generation. They must carry
    # their last cumulative count forward, NOT be read as zero -- otherwise the mean is biased
    # downward at late generations and the aggregate curve can spuriously decrease. See pipeline
    # audit 2026-07-13.
    gens_by_run = {r: sorted(byrun[r]) for r in byrun}
    def _cf(r, g):
        d = byrun[r]
        if g in d: return d[g]
        ks = [k for k in gens_by_run[r] if k <= g]
        return d[ks[-1]] if ks else 0
    def mean_at(g, c): return statistics.mean([_cf(r, g) for r in ecm if ecm[r] == c])
    print("\n### ASYMPTOTIC coverage over generations (close peaks, pooled scalars 0.5+1.0)")
    print(f"{'gen':>6} {'ECM':>6} {'noECM':>6} {'gap':>6}")
    xs = [100, 250, 500, 750, 1000, 1250, gmax]
    for g in xs:
        e, n = mean_at(g, "1"), mean_at(g, "0")
        print(f"{g:>6} {e:>6.2f} {n:>6.2f} {e-n:>6.2f}")
    print("=> if the gap stays wide at high g, coverage is not merely finite-time speed")
    if HAVE_PLT:
        gs = sorted(set(g for v in byrun.values() for g in v))
        gs = [g for g in gs if g % 10 == 0] + [gmax]
        fig, ax = plt.subplots(figsize=(5.6, 4.0))
        ax.plot(gs, [mean_at(g, "1") for g in gs], "-", color=COL["ecm"], label="error correction")
        ax.plot(gs, [mean_at(g, "0") for g in gs], "--", color=COL["no"], label="no correction")
        ax.axvline(500, color=COL["gray"], ls=":", lw=1)
        ax.text(500, 0.05, " original 500-gen budget", color=COL["gray"], fontsize=8)
        ax.set_xlabel("generation"); ax.set_ylabel("mean peaks colonized")
        ax.set_title("Coverage over an extended budget"); ax.set_ylim(0, None); ax.legend()
        fig.tight_layout(); fig.savefig(os.path.join(OUT, "figS_asymptotic.png"), dpi=300); plt.close(fig)
        print("figure -> figures/pub/figS_asymptotic.png")


def relaxed_colonization():
    print("\n### RELAXED colonization criterion (close peaks, scalar 1.0)")
    print("exact-match baseline (colon_fit 0.99999) = run2 pooled: ECM 0.90, noECM 0.38")
    for cf in ("0.90", "0.95"):
        rows = load(f"colon_{cf}")
        if not rows: print(f"  colon_{cf}: no data yet"); continue
        e = mse([float(r["final_peaks_colonized"]) for r in rows if E(r)])
        n = mse([float(r["final_peaks_colonized"]) for r in rows if N(r)])
        print(f"  colon_fit {cf}: ECM {e[0]:.2f}+-{e[1]:.2f}  noECM {n[0]:.2f}+-{n[1]:.2f}  gap {e[0]-n[0]:.2f}")
    print("=> if the ECM gap persists at relaxed thresholds, the finisher effect is not exact-match-specific")


def corrector_threshold():
    print("\n### CORRECTOR similarity-threshold sensitivity (close peaks, scalar 1.0)")
    for th in ("0.70", "0.80", "0.90"):
        rows = load(f"simthresh_{th}")
        if not rows: print(f"  simthresh_{th}: no data yet"); continue
        e = mse([float(r["final_peaks_colonized"]) for r in rows if E(r)])
        n = mse([float(r["final_peaks_colonized"]) for r in rows if N(r)])
        print(f"  threshold {th}: ECM {e[0]:.2f}+-{e[1]:.2f}  noECM {n[0]:.2f}+-{n[1]:.2f}  gap {e[0]-n[0]:.2f}")
    print("=> ECM advantage should be stable across thresholds if not a knife-edge of 0.8")


def multi_landscape():
    print("\n### MULTI-LANDSCAPE distance (3 peak-sets per level; de-confounds distance from peak identity)")
    for lvl in ("50", "60", "70"):
        print(f"  level ~{lvl}:")
        gaps = []
        for tag in (f"{lvl}a", f"{lvl}b", f"{lvl}c"):
            rows = load(os.path.join("multiland", tag))
            if not rows: print(f"    {tag}: no data yet"); continue
            e = statistics.mean([float(r["final_peaks_colonized"]) for r in rows if E(r)])
            n = statistics.mean([float(r["final_peaks_colonized"]) for r in rows if N(r)])
            gaps.append(e - n)
            print(f"    {tag}: ECM {e:.2f}  noECM {n:.2f}  gap {e-n:.2f}")
        if gaps:
            print(f"    -> gap across the 3 landscapes: {[round(g,2) for g in gaps]} (consistent sign = not peak-identity-specific)")


if __name__ == "__main__":
    asymptotic(); relaxed_colonization(); corrector_threshold(); multi_landscape()
