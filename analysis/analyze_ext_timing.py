"""Sweep 2 analysis: extinction recovery vs firing generation (fixed recovery window).

Reads data/stage2_ext_timing/gen*/stage2_summary.csv. Each firing generation G was
run with max_gens = G + 250, so every condition has the SAME 250-generation recovery
window; only the firing time differs. For each G, computes pre-extinction peaks
colonized (old cluster, at firing) and post-extinction peaks recolonized (new cluster,
by end), for ECM and no-ECM, ALL from the CSV. Sanity-checks that each folder's runs
carry the expected extinction_gen and a uniform code md5. Writes figures/stage2_ext_timing.png.
"""
import os, sys, csv, glob, json, statistics
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
PROJECT = os.path.dirname(HERE)
EDIR = os.path.join(PROJECT, "data", "stage2_ext_timing")


def fnum(x):
    try:
        return float(x)
    except (TypeError, ValueError):
        return float("nan")


def main():
    folders = sorted(glob.glob(os.path.join(EDIR, "gen*")),
                     key=lambda p: int(os.path.basename(p)[3:]))
    if not folders:
        sys.exit(f"no data in {EDIR}")
    md5s = set(); rows = []
    for fo in folders:
        G = int(os.path.basename(fo)[3:])
        man = json.load(open(os.path.join(fo, "manifest.json")))
        md5s.add(man["bfg_stage2_md5"])
        assert man["extinction_gen"] == G, f"{fo}: manifest ext_gen {man['extinction_gen']} != {G}"
        summ = list(csv.DictReader(open(os.path.join(fo, "stage2_summary.csv"))))
        pre = {0: [], 1: []}; post = {0: [], 1: []}
        for r in summ:
            e = int(r["use_ecm"])
            # every run must carry this firing gen (impossible-case guard)
            assert int(r["extinction_gen"]) == G, f"{fo}: row ext_gen != {G}"
            pre[e].append(fnum(r["pre_extinction_peaks_colonized"]))
            post[e].append(fnum(r["final_peaks_colonized"]))
        assert pre[0] and pre[1], f"missing a condition in {fo}"
        def se(v):
            return statistics.stdev(v) / (len(v) ** 0.5) if len(v) > 1 else 0.0
        post_gap = statistics.mean(post[1]) - statistics.mean(post[0])
        post_gap_se = (se(post[1]) ** 2 + se(post[0]) ** 2) ** 0.5
        rows.append({"G": G, "n_ecm": len(post[1]), "n_no": len(post[0]),
                     "pre_ecm": statistics.mean(pre[1]), "pre_no": statistics.mean(pre[0]),
                     "post_ecm": statistics.mean(post[1]), "post_ecm_se": se(post[1]),
                     "post_no": statistics.mean(post[0]), "post_no_se": se(post[0]),
                     "post_gap": post_gap, "post_gap_se": post_gap_se})
    assert len(md5s) == 1, f"MIXED code versions: {md5s}"
    print(f"code md5 (uniform): {list(md5s)[0][:12]}   recovery window = 250 gens (fixed)")
    print(f"{'fireG':>6} {'nE/nN':>7} | {'preECM':>7} {'preNo':>6} | {'postECM':>8} {'postNo':>7} {'postGap+-SE':>13}")
    for r in rows:
        print(f"{r['G']:>6} {r['n_ecm']:>3}/{r['n_no']:<3} | {r['pre_ecm']:>7.2f} {r['pre_no']:>6.2f} "
              f"| {r['post_ecm']:>8.2f} {r['post_no']:>7.2f} {r['post_gap']:>7.2f}+-{r['post_gap_se']:<4.2f}")

    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        x = [r["G"] for r in rows]
        fig, ax = plt.subplots(1, 2, figsize=(11, 4.2))
        ax[0].plot(x, [r["pre_ecm"] for r in rows], "o-", label="ECM", color="#1f77b4")
        ax[0].plot(x, [r["pre_no"] for r in rows], "s--", label="no ECM", color="#d62728")
        ax[0].set_xlabel("extinction firing generation")
        ax[0].set_ylabel("old peaks colonized at firing")
        ax[0].set_title("Pre-extinction (more climb time as G rises)")
        ax[0].legend(); ax[0].grid(alpha=.3)
        ax[1].plot(x, [r["post_ecm"] for r in rows], "o-", label="ECM", color="#1f77b4")
        ax[1].plot(x, [r["post_no"] for r in rows], "s--", label="no ECM", color="#d62728")
        ax[1].set_xlabel("extinction firing generation")
        ax[1].set_ylabel("new peaks recolonized (fixed 250-gen window)")
        ax[1].set_title("Post-extinction recovery"); ax[1].legend(); ax[1].grid(alpha=.3)
        fig.tight_layout()
        out = os.path.join(PROJECT, "figures", "stage2_ext_timing.png")
        fig.savefig(out, dpi=140); print(f"\nfigure -> {os.path.relpath(out, PROJECT)}")
    except Exception as e:
        print(f"(figure skipped: {e})")
    return rows


if __name__ == "__main__":
    main()
