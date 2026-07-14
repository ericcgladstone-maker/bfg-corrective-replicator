"""Generate publication-quality main figures (Figs 2-6) on pooled data, in the shared
pubfig style. Writes figures/pub/fig2..fig6 .png (300 dpi). All values from raw CSV."""
import os, sys, csv, glob, json, statistics, collections, itertools
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
PROJECT = os.path.dirname(HERE)
import pubfig, bfg_stage2 as s2, run_stage2 as r2
import matplotlib.pyplot as plt
pubfig.apply()
COL = pubfig.COL
OUT = os.path.join(PROJECT, "figures", "pub"); os.makedirs(OUT, exist_ok=True)
D = lambda *p: os.path.join(PROJECT, "data", *p)
E = lambda r: r["use_ecm"] == "1"; N = lambda r: r["use_ecm"] == "0"


def load(*folders):
    rows = []
    for f in folders:
        g = glob.glob(D(f, "*summary*.csv"))
        if g:
            rows += list(csv.DictReader(open(g[0])))
    return rows


def mse(vals):
    m = statistics.mean(vals)
    return m, (statistics.stdev(vals) / len(vals) ** 0.5 if len(vals) > 1 else 0)


# ---------- Fig 1: single-peak baseline (Stage 1 replication) ----------
def fig1():
    f = glob.glob(D("v6", "*full_1.csv")) or glob.glob(D("v6", "*full.csv"))
    rows = list(csv.DictReader(open(f[0])))
    scalars = sorted({float(r["mutation_scalar"]) for r in rows})
    # A: mean fitness over generations at a representative multiplier (1.0), ECM vs no
    rep = 1.0 if 1.0 in scalars else scalars[len(scalars) // 2]
    def traj(cond):
        byg = collections.defaultdict(list)
        for r in rows:
            if r["use_ecm"] == cond and abs(float(r["mutation_scalar"]) - rep) < 1e-9:
                byg[int(r["generation"])].append(float(r["mean_fitness"]))
        gs = sorted(byg)
        return gs, [statistics.mean(byg[g]) for g in gs]
    fig, ax = plt.subplots(1, 2, figsize=(9.2, 3.8))
    for cond, c, lab in [("1", COL["ecm"], "error correction"), ("0", COL["no"], "no correction")]:
        gs, ys = traj(cond)
        ax[0].plot(gs, ys, color=c, label=lab)
    ax[0].set_xlabel("generation"); ax[0].set_ylabel("mean fitness")
    ax[0].set_title(f"Faster climb with correction (multiplier {rep:g})")
    ax[0].legend(loc="lower right"); ax[0].set_ylim(0, 1); pubfig.panel(ax[0], "A")
    # B: final mean fitness by mutation multiplier, ECM vs no (mean over last 50 gens)
    gmax = max(int(r["generation"]) for r in rows)
    def final_by_scalar(cond):
        ms = []
        for sc in scalars:
            v = [float(r["mean_fitness"]) for r in rows
                 if r["use_ecm"] == cond and abs(float(r["mutation_scalar"]) - sc) < 1e-9
                 and int(r["generation"]) >= gmax - 50]
            ms.append(statistics.mean(v) if v else float("nan"))
        return ms
    for cond, c, lab, mk in [("1", COL["ecm"], "error correction", "o"), ("0", COL["no"], "no correction", "s")]:
        ax[1].plot(scalars, final_by_scalar(cond), mk + "-", color=c, label=lab)
    ax[1].set_xlabel("mutation rate multiplier"); ax[1].set_ylabel("final mean fitness")
    ax[1].set_title("Correction buffers against mutation")
    ax[1].set_xticks(scalars); ax[1].legend(loc="lower left"); ax[1].set_ylim(0, 1); pubfig.panel(ax[1], "B")
    print("fig1 ->", pubfig.finish(fig, os.path.join(OUT, "fig1_baseline.png")))


# ---------- Fig 2: multi-peak coverage ----------
def fig2():
    run2 = load("stage2_run2_fixed", "stage2_run2_v2")
    scalars = [0.25, 0.5, 1.0, 1.5]
    fig, ax = plt.subplots(1, 2, figsize=(9.2, 3.8))
    # A: mean peaks by mutation multiplier
    for cond, pred, c, lab, mk in [("e", E, COL["ecm"], "error correction", "o"),
                                    ("n", N, COL["no"], "no correction", "s")]:
        ms, es = [], []
        for sc in scalars:
            v = [float(r["final_peaks_colonized"]) for r in run2
                 if pred(r) and abs(float(r["mutation_scalar"]) - sc) < 1e-9]
            m, e = mse(v); ms.append(m); es.append(1.96 * e)  # 95% CI
        ax[0].errorbar(scalars, ms, es, fmt=mk + "-", color=c, label=lab, capsize=3)
    ax[0].set_xlabel("mutation rate multiplier")
    ax[0].set_ylabel("mean peaks colonized")
    ax[0].set_title("Coverage rises then falls with noise")
    ax[0].set_xticks(scalars); ax[0].legend(loc="upper right")
    ax[0].set_ylim(0, None); pubfig.panel(ax[0], "A")
    # B: distribution of peaks colonized per run
    ks = [0, 1, 2, 3]
    import numpy as np
    width = 0.38
    for off, pred, c, lab in [(-width / 2, E, COL["ecm"], "error correction"),
                              (width / 2, N, COL["no"], "no correction")]:
        vals = [float(r["final_peaks_colonized"]) for r in run2 if pred(r)]
        n = len(vals)
        frac = [sum(1 for x in vals if round(x) == k) / n for k in ks]
        ax[1].bar([k + off for k in ks], frac, width, color=c, label=lab)
    ax[1].set_xlabel("peaks colonized in a run")
    ax[1].set_ylabel("fraction of runs")
    ax[1].set_title("Correction reaches more peaks per run")
    ax[1].set_xticks(ks); ax[1].set_xticklabels(["0", "1", "2", "3"])
    ax[1].legend(loc="upper right"); pubfig.panel(ax[1], "B")
    print("fig2 ->", pubfig.finish(fig, os.path.join(OUT, "fig2_coverage.png")))


# ---------- Fig 3: coverage vs inter-peak distance ----------
def fig3():
    _, _, _, targets = r2.load_real_data(); lev = s2.levenshtein
    def mpw(idx):
        return sum(lev(targets[a], targets[b]) for a, b in itertools.combinations(idx, 2)) / 10
    rows = []
    for fo in sorted(glob.glob(D("stage2_distance", "mpw*"))):
        man = json.load(open(os.path.join(fo, "manifest.json")))
        summ = [r for r in csv.DictReader(open(os.path.join(fo, "stage2_summary.csv")))
                if r["valley_reaper"] == "top_fitness"]  # ECM-vs-no comparison at fitness pruning
        e = mse([float(r["final_peaks_colonized"]) for r in summ if E(r)])
        n = mse([float(r["final_peaks_colonized"]) for r in summ if N(r)])
        rows.append((mpw(man["peak_indices"]), e, n))
    rows.sort()
    x = [r[0] for r in rows]
    fig, ax = plt.subplots(figsize=(5.2, 4.0))
    ax.errorbar(x, [r[1][0] for r in rows], [r[1][1] for r in rows], fmt="o-", color=COL["ecm"], label="error correction")
    ax.errorbar(x, [r[2][0] for r in rows], [r[2][1] for r in rows], fmt="s--", color=COL["no"], label="no correction")
    ax.set_xlabel("mean inter-peak distance (edits)")
    ax.set_ylabel("mean peaks colonized")
    ax.set_title("Advantage holds as peaks spread apart")
    ax.set_ylim(0, None); ax.legend()
    print("fig3 ->", pubfig.finish(fig, os.path.join(OUT, "fig3_distance.png")))


# ---------- Fig 4: reaper ease-asymmetry gradient ----------
def fig4():
    _, _, _, targets = r2.load_real_data(); lev = s2.levenshtein
    def mpw(idx):
        return sum(lev(targets[a], targets[b]) for a, b in itertools.combinations(idx, 2)) / 10
    rows = []
    for fo in sorted(glob.glob(D("stage2_distance", "mpw*"))):
        man = json.load(open(os.path.join(fo, "manifest.json")))
        summ = list(csv.DictReader(open(os.path.join(fo, "stage2_summary.csv"))))
        tf = mse([float(r["final_peaks_colonized"]) for r in summ if E(r) and r["valley_reaper"] == "top_fitness"])
        rd = mse([float(r["final_peaks_colonized"]) for r in summ if E(r) and r["valley_reaper"] == "random"])
        rows.append((mpw(man["peak_indices"]), tf, rd))
    rows.sort()
    x = [r[0] for r in rows]
    fig, ax = plt.subplots(1, 2, figsize=(9.2, 3.8))
    import numpy as np
    tf_y = [r[1][0] for r in rows]; rd_y = [r[2][0] for r in rows]
    # faint linear-trend lines to show random declines while fitness stays flat
    xx = np.linspace(min(x), max(x), 50)
    for y, c in [(tf_y, COL["ecm"]), (rd_y, COL["no"])]:
        b1, b0 = np.polyfit(x, y, 1)
        ax[0].plot(xx, b0 + b1 * xx, color=c, lw=1.2, alpha=0.35, zorder=1)
    ax[0].errorbar(x, tf_y, [r[1][1] for r in rows], fmt="o-", color=COL["ecm"], label="fitness pruning", zorder=3)
    ax[0].errorbar(x, rd_y, [r[2][1] for r in rows], fmt="s--", color=COL["no"], label="random pruning", zorder=3)
    ax[0].set_xlabel("mean inter-peak distance (edits)")
    ax[0].set_ylabel("mean peaks colonized")
    ax[0].set_title("Fitness pruning retains coverage as peaks spread apart")
    ax[0].set_ylim(0, None); ax[0].legend(); pubfig.panel(ax[0], "A")
    adv = [r[1][0] - r[2][0] for r in rows]
    adv_se = [(r[1][1] ** 2 + r[2][1] ** 2) ** 0.5 for r in rows]
    ax[1].errorbar(x, adv, adv_se, fmt="D-", color=COL["accent"])
    ax[1].axhline(0, color=COL["gray"], lw=0.8)
    ax[1].set_xlabel("mean inter-peak distance (edits)")
    ax[1].set_ylabel("fitness-pruning advantage")
    ax[1].set_title("Fitness-pruning advantage across inter-peak distance"); pubfig.panel(ax[1], "B")
    print("fig4 ->", pubfig.finish(fig, os.path.join(OUT, "fig4_reaper.png")))


# ---------- Fig 5: niche capacity ----------
def fig5():
    sl = load("stage2_slots", "stage2_slots_v2")
    slots = [5, 10, 20, 40]
    fig, ax = plt.subplots(figsize=(5.2, 4.0))
    for pred, c, lab, mk in [(E, COL["ecm"], "error correction", "o"), (N, COL["no"], "no correction", "s")]:
        ms, es = [], []
        for s in slots:
            v = [float(r["final_peaks_colonized"]) for r in sl if pred(r) and int(r["slots_per_peak"]) == s]
            m, e = mse(v); ms.append(m); es.append(e)
        ax.errorbar(slots, ms, es, fmt=mk + "-", color=c, label=lab)
    ax.set_xlabel("genotype slots per peak (niche capacity)")
    ax.set_ylabel("mean peaks colonized")
    ax.set_title("Correction helps most at moderate capacity")
    ax.set_xticks(slots); ax.set_ylim(0, None); ax.legend()
    print("fig5 ->", pubfig.finish(fig, os.path.join(OUT, "fig5_capacity.png")))


# ---------- Fig 6: recovery after disruption ----------
def fig6():
    pg = list(csv.DictReader(open(D("stage2_ext_window", "stage2_per_generation.csv"))))
    G = 250
    byrun = collections.defaultdict(dict); ecm = {}
    for r in pg:
        byrun[r["run_id"]][int(r["generation"])] = int(r["peaks_colonized"]); ecm[r["run_id"]] = r["use_ecm"]
    xs = list(range(G, 1000, 25)) + [999]
    # peaks_colonized is cumulative: carry a terminated run's last count forward rather than
    # reading absent late generations as zero (pipeline audit 2026-07-13). No run terminates early
    # in this dataset, so this is identical to the prior output here, but it is the correct rule.
    gens_by_run = {r: sorted(byrun[r]) for r in byrun}
    def _cf(r, g):
        d = byrun[r]
        if g in d: return d[g]
        ks = [k for k in gens_by_run[r] if k <= g]
        return d[ks[-1]] if ks else 0
    def mean_at(g, cond):
        return statistics.mean([_cf(r, g) for r in ecm if ecm[r] == cond])
    fig, ax = plt.subplots(figsize=(5.6, 4.0))
    ax.plot([g - G for g in xs], [mean_at(g, "1") for g in xs], "o-", color=COL["ecm"], ms=4, label="error correction")
    ax.plot([g - G for g in xs], [mean_at(g, "0") for g in xs], "s--", color=COL["no"], ms=4, label="no correction")
    ax.axvline(250, color=COL["gray"], ls=":", lw=1.2)
    ax.text(250, ax.get_ylim()[1] * 0.05, " earlier 250-gen cutoff", color=COL["gray"], fontsize=9)
    ax.set_xlabel("generations after disruption")
    ax.set_ylabel("new peaks recolonized")
    ax.set_title("Correction's recovery advantage grows over time")
    ax.set_ylim(0, None); ax.legend(loc="upper left")
    print("fig6 ->", pubfig.finish(fig, os.path.join(OUT, "fig6_recovery.png")))


# ---------- SI Fig: colonization sources ----------
def figS_sources():
    run2 = load("stage2_run2_fixed", "stage2_run2_v2")
    cats = [("valley", "valley arrival"), ("in_situ", "in-place maturation"), ("peak", "peak-to-peak")]
    def counts(pred):
        c = collections.Counter()
        for r in run2:
            if not pred(r):
                continue
            for v in json.loads(r["colonization_source"] or "{}").values():
                c["peak" if v.startswith("peak:") else v] += 1
        t = sum(c.values()) or 1
        return [100 * c[k] / t for k, _ in cats]
    import numpy as np
    xpos = np.arange(len(cats)); w = 0.38
    fig, ax = plt.subplots(figsize=(5.6, 4.0))
    ax.bar(xpos - w / 2, counts(E), w, color=COL["ecm"], label="error correction")
    ax.bar(xpos + w / 2, counts(N), w, color=COL["no"], label="no correction")
    ax.set_xticks(xpos); ax.set_xticklabels([lab for _, lab in cats])
    ax.set_ylabel("percent of colonizations")
    ax.set_title("Peaks are reached from the valley or in place, never by leaping")
    ax.legend()
    print("figS_sources ->", pubfig.finish(fig, os.path.join(OUT, "figS_sources.png")))


# ---------- SI Fig: extinction-timing robustness ----------
def figS_exttiming():
    import glob as _g
    folders = sorted(_g.glob(D("stage2_ext_timing", "gen*")), key=lambda p: int(os.path.basename(p)[3:]))
    G, pre_e, pre_n, post_e, post_n = [], [], [], [], []
    for fo in folders:
        g = int(os.path.basename(fo)[3:]); G.append(g)
        summ = list(csv.DictReader(open(os.path.join(fo, "stage2_summary.csv"))))
        pre_e.append(statistics.mean([float(r["pre_extinction_peaks_colonized"]) for r in summ if E(r)]))
        pre_n.append(statistics.mean([float(r["pre_extinction_peaks_colonized"]) for r in summ if N(r)]))
        post_e.append(statistics.mean([float(r["final_peaks_colonized"]) for r in summ if E(r)]))
        post_n.append(statistics.mean([float(r["final_peaks_colonized"]) for r in summ if N(r)]))
    fig, ax = plt.subplots(1, 2, figsize=(9.2, 3.8))
    ax[0].plot(G, pre_e, "o-", color=COL["ecm"], label="error correction")
    ax[0].plot(G, pre_n, "s--", color=COL["no"], label="no correction")
    ax[0].set_xlabel("disruption generation"); ax[0].set_ylabel("old peaks held at disruption")
    ax[0].set_title("Pre-disruption advantage is robust"); ax[0].set_ylim(0, None)
    ax[0].legend(); pubfig.panel(ax[0], "A")
    ax[1].plot(G, post_e, "o-", color=COL["ecm"], label="error correction")
    ax[1].plot(G, post_n, "s--", color=COL["no"], label="no correction")
    ax[1].set_xlabel("disruption generation"); ax[1].set_ylabel("new peaks recovered (250-gen window)")
    ax[1].set_title("Recovery is small in a short window"); ax[1].set_ylim(0, None)
    ax[1].legend(); pubfig.panel(ax[1], "B")
    print("figS_exttiming ->", pubfig.finish(fig, os.path.join(OUT, "figS_exttiming.png")))


if __name__ == "__main__":
    fig2(); fig3(); fig4(); fig5(); fig6(); figS_sources(); figS_exttiming()
    print("\nall publication figures written to figures/pub/")
