"""Sweep 3 analysis: blanketing vs inter-peak distance.

Reads data/stage2_distance/mpw*/stage2_summary.csv (all produced by the current
bfg_stage2.py). For each distance level, computes mean peaks colonized for ECM
and no-ECM, plus the gap, ALL from the CSV. Recomputes each level's mean pairwise
Levenshtein distance from the manifest peak_indices as an independent check on the
folder label. Sanity-checks cell counts and that every manifest shares one code md5.
Writes figures/stage2_distance.png.
"""
import os, sys, csv, glob, json, itertools, statistics
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
PROJECT = os.path.dirname(HERE)
import bfg_stage2 as s2
import run_stage2 as r2

DDIR = os.path.join(PROJECT, "data", "stage2_distance")


def mean_pairwise(idx, targets, lev):
    ds = [lev(targets[a], targets[b]) for a, b in itertools.combinations(idx, 2)]
    return sum(ds) / len(ds)


def main():
    _, _, _, targets = r2.load_real_data()
    lev = s2.levenshtein
    folders = sorted(glob.glob(os.path.join(DDIR, "mpw*")))
    if not folders:
        sys.exit(f"no data in {DDIR}")
    md5s = set()
    rows = []
    for fo in folders:
        man = json.load(open(os.path.join(fo, "manifest.json")))
        md5s.add(man["bfg_stage2_md5"])
        idx = man["peak_indices"]
        mpw = mean_pairwise(idx, targets, lev)
        summ = list(csv.DictReader(open(os.path.join(fo, "stage2_summary.csv"))))
        by = {0: [], 1: []}
        for r in summ:
            by[int(r["use_ecm"])].append(float(r["final_peaks_colonized"]))
        assert by[0] and by[1], f"missing a condition in {fo}"
        def se(v):
            return statistics.stdev(v) / (len(v) ** 0.5) if len(v) > 1 else 0.0
        ecm_m = statistics.mean(by[1]); no_m = statistics.mean(by[0])
        gap_se = (se(by[1]) ** 2 + se(by[0]) ** 2) ** 0.5
        rows.append({"mpw": mpw, "label": os.path.basename(fo), "idx": idx,
                     "n_ecm": len(by[1]), "n_no": len(by[0]),
                     "ecm": ecm_m, "ecm_se": se(by[1]), "no": no_m, "no_se": se(by[0]),
                     "gap": ecm_m - no_m, "gap_se": gap_se})
    assert len(md5s) == 1, f"MIXED code versions across levels: {md5s}"
    rows.sort(key=lambda r: r["mpw"])

    print(f"code md5 (uniform): {list(md5s)[0][:12]}")
    print(f"{'mpw':>6} {'peaks':>20} {'nE/nN':>7} {'ECM+-SE':>13} {'noECM+-SE':>13} {'gap+-SE':>13}")
    for r in rows:
        print(f"{r['mpw']:>6.1f} {str(r['idx']):>20} {r['n_ecm']:>3}/{r['n_no']:<3} "
              f"{r['ecm']:>5.2f}+-{r['ecm_se']:<4.2f}  {r['no']:>5.2f}+-{r['no_se']:<4.2f}  "
              f"{r['gap']:>5.2f}+-{r['gap_se']:<4.2f}")

    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        x = [r["mpw"] for r in rows]
        fig, ax = plt.subplots(1, 2, figsize=(11, 4.2))
        ax[0].errorbar(x, [r["ecm"] for r in rows], yerr=[r["ecm_se"] for r in rows],
                       fmt="o-", capsize=3, label="error correction", color="#1f77b4")
        ax[0].errorbar(x, [r["no"] for r in rows], yerr=[r["no_se"] for r in rows],
                       fmt="s--", capsize=3, label="no correction", color="#d62728")
        ax[0].set_xlabel("mean pairwise inter-peak distance (Levenshtein)")
        ax[0].set_ylabel("mean peaks colonized")
        ax[0].set_title("Blanketing vs inter-peak distance"); ax[0].legend(); ax[0].grid(alpha=.3)
        ax[1].plot(x, [r["gap"] for r in rows], "d-", color="#2ca02c")
        ax[1].set_xlabel("mean pairwise inter-peak distance (Levenshtein)")
        ax[1].set_ylabel("ECM advantage (mean peaks, ECM - no)")
        ax[1].set_title("Correction advantage vs distance"); ax[1].grid(alpha=.3)
        ax[1].axhline(0, color="k", lw=.6)
        fig.tight_layout()
        out = os.path.join(PROJECT, "figures", "stage2_distance.png")
        fig.savefig(out, dpi=140); print(f"\nfigure -> {os.path.relpath(out, PROJECT)}")
    except Exception as e:
        print(f"(figure skipped: {e})")
    return rows


if __name__ == "__main__":
    main()
