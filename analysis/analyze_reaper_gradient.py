"""Reaper ease-asymmetry gradient: across the 6 distance-ladder peak sets, compare the
two valley pruning rules on (1) total coverage, (2) reach to the hardest peaks, and (3)
evenness of colonization across peaks. Tests whether the fitness-pruning advantage grows
with asymmetry (peaks less equally reachable), reversing the 'random preserves diversity'
intuition. All from CSV, with standard errors. Writes figures/stage2_reaper_gradient.png.

'Asymmetry' proxy: mean pairwise Levenshtein distance of the peak set (46 close .. 72 far),
which we already use as the distance axis; farther sets are more unequally reachable.
"""
import os, sys, csv, glob, json, statistics, collections, itertools, math
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
PROJECT = os.path.dirname(HERE)
import bfg_stage2 as s2, run_stage2 as r2

DDIR = os.path.join(PROJECT, "data", "stage2_distance")
E = lambda r: r["use_ecm"] == "1"
TF = lambda r: r["valley_reaper"] == "top_fitness"
RD = lambda r: r["valley_reaper"] == "random"


def se(v):
    return statistics.stdev(v) / len(v) ** 0.5 if len(v) > 1 else 0.0


def main():
    _, _, _, targets = r2.load_real_data()
    lev = s2.levenshtein
    def mpw(idx):
        ds = [lev(targets[a], targets[b]) for a, b in itertools.combinations(idx, 2)]
        return sum(ds) / len(ds)

    rows = []
    for fo in sorted(glob.glob(os.path.join(DDIR, "mpw*"))):
        man = json.load(open(os.path.join(fo, "manifest.json")))
        idx = man["peak_indices"]
        summ = list(csv.DictReader(open(os.path.join(fo, "stage2_summary.csv"))))
        # ECM only for the clean comparison
        def cover(pred):
            v = [float(r["final_peaks_colonized"]) for r in summ if pred(r) and E(r)]
            return (statistics.mean(v), se(v), len(v)) if v else (None, None, 0)
        # per-peak position histogram (0=easiest-reachable ordering not guaranteed; report raw)
        def hist(pred):
            c = collections.Counter()
            for r in summ:
                if pred(r) and E(r):
                    for k in json.loads(r["per_peak_convergence"] or "{}"):
                        c[int(k)] += 1
            return [c.get(i, 0) for i in range(len(idx))]
        tf_m = cover(TF); rd_m = cover(RD)
        if rd_m[2] == 0:
            continue  # random not run yet for this level
        htf, hrd = hist(TF), hist(RD)
        def entropy(h):
            t = sum(h)
            ps = [x / t for x in h if x > 0]
            return -sum(p * math.log(p, 2) for p in ps) if ps else 0
        rows.append({"mpw": mpw(idx), "idx": idx,
                     "tf": tf_m[0], "tf_se": tf_m[1], "rd": rd_m[0], "rd_se": rd_m[1],
                     "adv": tf_m[0] - rd_m[0], "adv_se": (tf_m[1] ** 2 + rd_m[1] ** 2) ** 0.5,
                     "H_tf": entropy(htf), "H_rd": entropy(hrd),
                     "hist_tf": htf, "hist_rd": hrd})
    rows.sort(key=lambda r: r["mpw"])
    if not rows:
        sys.exit("no levels have the random reaper yet")

    print(f"{'mpw':>5} {'fitness':>13} {'random':>13} {'fit-adv':>13} {'H_fit':>6} {'H_rnd':>6}")
    for r in rows:
        print(f"{r['mpw']:>5.0f} {r['tf']:>6.2f}+-{r['tf_se']:<4.2f} {r['rd']:>6.2f}+-{r['rd_se']:<4.2f} "
              f"{r['adv']:>6.2f}+-{r['adv_se']:<4.2f} {r['H_tf']:>6.2f} {r['H_rd']:>6.2f}")
    print("\nprediction: if narrative RIGHT, random should catch up / overtake at high mpw;")
    print("if REVERSED, fitness advantage GROWS with mpw (asymmetry).")

    try:
        import matplotlib; matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        x = [r["mpw"] for r in rows]
        fig, ax = plt.subplots(1, 2, figsize=(11, 4.2))
        ax[0].errorbar(x, [r["tf"] for r in rows], [r["tf_se"] for r in rows], fmt="o-", capsize=3,
                       label="fitness pruning", color="#1f77b4")
        ax[0].errorbar(x, [r["rd"] for r in rows], [r["rd_se"] for r in rows], fmt="s--", capsize=3,
                       label="random pruning", color="#d62728")
        ax[0].set_xlabel("mean inter-peak distance (asymmetry proxy)")
        ax[0].set_ylabel("mean peaks colonized (ECM)")
        ax[0].set_title("Coverage by valley reaper vs asymmetry"); ax[0].legend(); ax[0].grid(alpha=.3)
        ax[1].errorbar(x, [r["adv"] for r in rows], [r["adv_se"] for r in rows], fmt="d-", capsize=3,
                       color="#2ca02c")
        ax[1].axhline(0, color="k", lw=.6)
        ax[1].set_xlabel("mean inter-peak distance (asymmetry proxy)")
        ax[1].set_ylabel("fitness-pruning advantage (fitness - random)")
        ax[1].set_title("Fitness advantage grows with asymmetry?"); ax[1].grid(alpha=.3)
        fig.tight_layout()
        out = os.path.join(PROJECT, "figures", "stage2_reaper_gradient.png")
        fig.savefig(out, dpi=140); print(f"\nfigure -> {os.path.relpath(out, PROJECT)}")
    except Exception as e:
        print(f"(figure skipped: {e})")


if __name__ == "__main__":
    main()
