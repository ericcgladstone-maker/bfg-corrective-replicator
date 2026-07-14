"""Restructured main-text figures (2026-07-13 visual pass). Builds the mechanism, robustness,
and boundary-condition figures that foreground the paper's two sharpest contributions (why
correction helps, when it fails). All data from existing raw CSV; no new runs. Style via pubfig.

New main-text lineup:
  Fig 3  fig3_coverage.png   headline multi-peak result (run-level + 95% CI)
  Fig 4  fig4_robustness.png time-to-coverage + nine independently-sampled landscapes
  Fig 5  fig5_mechanism.png  finishing mechanism (band entry, conditional completion, timing, sources)
  Fig 6  fig6_boundary.png   niche capacity + codebook-alignment necessity test
Pruning and disruption move to the SI (figS_pruning.png, figS_recovery.png already exist).
"""
import os, sys, csv, glob, json, collections, statistics, math
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
ROOT = os.path.dirname(HERE)
import pubfig, matplotlib.pyplot as plt, numpy as np
import bfg_stage2 as s2
pubfig.apply(); COL = pubfig.COL
D = lambda *p: os.path.join(ROOT, "data", *p)
OUT = os.path.join(ROOT, "figures", "pub")
E = lambda r: r["use_ecm"] == "1"


def load(*folders):
    rows = []
    for f in folders:
        g = glob.glob(D(f, "stage2_summary.csv"))
        if g:
            rows += list(csv.DictReader(open(g[0])))
    return rows


def mse(v):
    return (statistics.mean(v), statistics.stdev(v) / len(v) ** 0.5) if len(v) > 1 else (v[0] if v else 0, 0)


def wilson(k, n):
    """Wilson 95% interval for a proportion; returns (p, lo, hi)."""
    if n == 0:
        return 0, 0, 0
    p = k / n; z = 1.96
    d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return p, max(0, c - h), min(1, c + h)


def pergen(folder):
    """run_id -> sorted list of (gen, mean_fit, max_fit, n_full, peaks); plus ecm map."""
    byrun = collections.defaultdict(list); ecm = {}
    for r in csv.DictReader(open(D(folder, "stage2_per_generation.csv"))):
        byrun[r["run_id"]].append((int(r["generation"]), float(r["mean_fitness"]),
                                   float(r["max_fitness"]), int(r["n_full_fit"]), int(r["peaks_colonized"])))
        ecm[r["run_id"]] = r["use_ecm"]
    for r in byrun:
        byrun[r].sort()
    return byrun, ecm


def mean_pairwise_distance(peaks):
    d = [s2.levenshtein(peaks[i], peaks[j]) for i in range(len(peaks)) for j in range(i + 1, len(peaks))]
    return statistics.mean(d)


# ============================ Fig 4: temporal + landscape robustness ============================
def fig_robustness():
    fig, ax = plt.subplots(1, 2, figsize=(9.4, 4.0))
    # Panel A: time to coverage (cumulative incidence of reaching >=1 and >=2 peaks)
    byrun = collections.defaultdict(dict); ecm = {}
    for r in csv.DictReader(open(D("asymptotic", "stage2_per_generation.csv"))):
        byrun[r["run_id"]][int(r["generation"])] = int(r["peaks_colonized"]); ecm[r["run_id"]] = r["use_ecm"]
    gmax = max(max(v) for v in byrun.values())
    gens_by = {r: sorted(byrun[r]) for r in byrun}
    def cf(r, g):
        d = byrun[r]
        if g in d: return d[g]
        ks = [k for k in gens_by[r] if k <= g]
        return d[ks[-1]] if ks else 0
    gs = list(range(0, gmax + 1, 20))
    def frac(cond, k): return [statistics.mean([1.0 if cf(r, g) >= k else 0.0 for r in ecm if ecm[r] == cond]) for g in gs]
    # color encodes condition, line style encodes the coverage threshold
    ax[0].plot(gs, frac("1", 1), "-", color=COL["ecm"], lw=2.3, label="correction, ≥1 peak")
    ax[0].plot(gs, frac("0", 1), "-", color=COL["no"], lw=2.3, label="no correction, ≥1 peak")
    ax[0].plot(gs, frac("1", 2), "--", color=COL["ecm"], lw=2.0, label="correction, ≥2 peaks")
    ax[0].plot(gs, frac("0", 2), "--", color=COL["no"], lw=2.0, label="no correction, ≥2 peaks")
    ax[0].axvline(500, color=COL["gray"], ls=":", lw=1.3)
    ax[0].text(512, 0.02, "standard horizon", color=COL["gray"], fontsize=8, rotation=90, va="bottom", ha="left")
    ax[0].set_xlabel("generation"); ax[0].set_ylabel("fraction of runs reaching the coverage")
    ax[0].set_ylim(0, 1.02); ax[0].legend(fontsize=8.5, loc="lower right", title="solid: ≥1 peak   dashed: ≥2 peaks", title_fontsize=8)
    pubfig.panel(ax[0], "A")
    # Panel B: nine independently sampled landscapes; advantage vs mean inter-peak distance
    xs, ys, es, lv = [], [], [], []
    for lvl in ("50", "60", "70"):
        for tag in (lvl + "a", lvl + "b", lvl + "c"):
            rows = load(os.path.join("multiland", tag))
            if not rows: continue
            man = json.load(open(D("multiland", tag, "manifest.json")))
            dist = mean_pairwise_distance(man["peaks"])
            em, ee = mse([float(r["final_peaks_colonized"]) for r in rows if E(r)])
            nm, ne = mse([float(r["final_peaks_colonized"]) for r in rows if not E(r)])
            xs.append(dist); ys.append(em - nm); es.append(1.96 * math.sqrt(ee ** 2 + ne ** 2)); lv.append(lvl)
    ax[1].axhline(0, color=COL["gray"], lw=1)
    rng = np.random.default_rng(7)
    xj = [x + rng.uniform(-0.7, 0.7) for x in xs]
    ax[1].errorbar(xj, ys, yerr=es, fmt="o", color=COL["ecm"], ms=6, elinewidth=1.2, capsize=3, alpha=0.85,
                   label="individual landscapes")
    for lvl in ("50", "60", "70"):
        idx = [i for i, l in enumerate(lv) if l == lvl]
        if idx:
            mx = statistics.mean([xs[i] for i in idx]); my = statistics.mean([ys[i] for i in idx])
            ax[1].plot(mx, my, "D", color=COL["accent"], ms=11, markeredgecolor="k", markeredgewidth=1.2,
                       zorder=6, label="mean at distance" if lvl == "50" else None)
    ax[1].set_xlabel("mean inter-peak distance (edits)")
    ax[1].set_ylabel("correction advantage (peaks colonized)")
    ax[1].set_ylim(min(-0.15, min(ys) - 0.2), None); ax[1].legend(fontsize=8.5, loc="upper right")
    pubfig.panel(ax[1], "B")
    print("fig4_robustness ->", pubfig.finish(fig, os.path.join(OUT, "fig4_robustness.png")))


# ============================ Fig 5: finishing mechanism ============================
def fig_mechanism():
    BAND = 0.90
    byrun, ecm = pergen("stage2_run2_fixed")
    def entered(r): return any(mf >= BAND for _, _, mf, _, _ in byrun[r])
    def completed(r): return byrun[r][-1][4] >= 1
    def band_gen(r): return next((g for g, _, mf, _, _ in byrun[r] if mf >= BAND), None)
    def comp_gen(r): return next((g for g, _, _, _, pc in byrun[r] if pc >= 1), None)
    runs = {c: [r for r in ecm if ecm[r] == c] for c in ("1", "0")}
    fig, ax = plt.subplots(1, 4, figsize=(13.2, 3.6))
    labels = ["correction", "no\ncorrection"]; xc = [0, 1]; cols = [COL["ecm"], COL["no"]]
    # A: P(reach near-target band); n/N denominators shown, Wilson 95% intervals
    for i, c in enumerate(("1", "0")):
        N = len(runs[c]); k = sum(entered(r) for r in runs[c]); p, lo, hi = wilson(k, N)
        ax[0].bar(xc[i], p, color=cols[i], width=0.6)
        ax[0].errorbar(xc[i], p, yerr=[[p - lo], [hi - p]], color="k", capsize=4, lw=1.2)
        ax[0].text(xc[i], min(hi + 0.03, 1.0), f"{k}/{N}", ha="center", va="bottom", fontsize=9)
    ax[0].set_xticks(xc); ax[0].set_xticklabels(labels); ax[0].set_ylim(0, 1.1)
    ax[0].set_ylabel("P(reach near-target band, ≥0.90)"); pubfig.panel(ax[0], "A")
    # B: P(complete | entered band) -- conditional, descriptive; n/N denominators shown
    for i, c in enumerate(("1", "0")):
        ent = [r for r in runs[c] if entered(r)]; N = len(ent)
        k = sum(completed(r) for r in ent); p, lo, hi = wilson(k, N)
        ax[1].bar(xc[i], p, color=cols[i], width=0.6)
        ax[1].errorbar(xc[i], p, yerr=[[p - lo], [hi - p]], color="k", capsize=4, lw=1.2)
        ax[1].text(xc[i], hi + 0.03, f"{k}/{N}", ha="center", va="bottom", fontsize=9)
    ax[1].set_xticks(xc); ax[1].set_xticklabels(labels); ax[1].set_ylim(0, 1.1)
    ax[1].set_ylabel("P(exact match | band entry)\n(conditional, descriptive)"); pubfig.panel(ax[1], "B")
    # C: time from band entry to exact match (ECDF), risk set = runs that entered band AND completed
    ax[2].axhline(0.5, color=COL["light"], lw=0.9, ls="--")
    for i, c in enumerate(("1", "0")):
        dt = [comp_gen(r) - band_gen(r) for r in runs[c]
              if entered(r) and completed(r) and band_gen(r) is not None and comp_gen(r) is not None
              and comp_gen(r) >= band_gen(r)]
        if dt:
            xs = sorted(dt); ys = [(j + 1) / len(xs) for j in range(len(xs))]
            med = statistics.median(dt)
            ax[2].step([0] + xs, [0] + ys, where="post", color=cols[i], lw=2.2,
                       label=f"{labels[i].replace(chr(10), ' ')} (median {int(med)}, n={len(dt)})")
            ax[2].plot([med, med], [0, 0.5], color=cols[i], ls=":", lw=1.4)
    ax[2].set_xlabel("generations from band entry to exact match"); ax[2].set_ylabel("cumulative fraction")
    ax[2].set_ylim(0, 1); ax[2].legend(fontsize=8, loc="lower right"); pubfig.panel(ax[2], "C")
    # D: colonization sources -- counts with within-condition percentages annotated
    src = {c: collections.Counter() for c in ("1", "0")}
    for r in load("stage2_run2_fixed", "stage2_run2_v2"):
        c = r["use_ecm"]
        for _, s in json.loads(r["colonization_source"] or "{}").items():
            src[c]["peak" if s.startswith("peak") else s] += 1
    cats = ["valley", "in_situ", "peak"]; catlab = ["valley\narrival", "in-place\nmaturation", "peak\ntransfer"]
    w = 0.38; x = np.arange(len(cats)); ymax = max(max(src["1"].values()), max(src["0"].values()))
    for i, c in enumerate(("1", "0")):
        tot = sum(src[c][k] for k in cats) or 1
        vals = [src[c][k] for k in cats]
        ax[3].bar(x + (i - 0.5) * w, vals, width=w, color=cols[i], label=labels[i].replace("\n", " "))
        for xi, v in zip(x, vals):
            if v > 0:
                ax[3].text(xi + (i - 0.5) * w, v + ymax * 0.015, f"{v}\n{100*v/tot:.0f}%", ha="center",
                           va="bottom", fontsize=7.5, color=cols[i])
    ax[3].set_xticks(x); ax[3].set_xticklabels(catlab); ax[3].set_ylabel("colonizations (count; % = within-condition share)")
    ax[3].set_ylim(0, ymax * 1.28); ax[3].legend(fontsize=9); pubfig.panel(ax[3], "D")
    print("fig5_mechanism ->", pubfig.finish(fig, os.path.join(OUT, "fig5_mechanism.png")))


# ============================ Fig 6: boundary conditions ============================
def fig_boundary():
    fig, ax = plt.subplots(1, 3, figsize=(13.0, 3.9))
    # A: niche capacity
    sl = load("stage2_slots", "stage2_slots_v2")
    slots = sorted({int(r["slots_per_peak"]) for r in sl})
    for cond, col, lab, ls in [("1", COL["ecm"], "correction", "-"), ("0", COL["no"], "no correction", "--")]:
        ms, es = [], []
        for s in slots:
            v = [float(r["final_peaks_colonized"]) for r in sl if r["use_ecm"] == cond and int(r["slots_per_peak"]) == s]
            m, e = mse(v); ms.append(m); es.append(1.96 * e)
        ax[0].errorbar(slots, ms, yerr=es, fmt="o" + ls, color=col, label=lab, capsize=3)
    ax[0].set_xlabel("slots per peak"); ax[0].set_ylabel("mean peaks colonized")
    ax[0].set_xticks(slots); ax[0].set_ylim(0, None); ax[0].legend(); pubfig.panel(ax[0], "A")
    # B & C: codebook-alignment necessity (peaks colonized, and max attainable fitness)
    full = load("simthresh_0.80"); abl = load("dict_ablation")
    def peaks(rows, ecm): return [float(r["final_peaks_colonized"]) for r in rows if r["use_ecm"] == ecm]
    conds = [("full-dict\ncorrection", peaks(full, "1"), COL["ecm"]),
             ("reduced-dict\ncorrection", peaks(abl, "1"), COL["accent"]),
             ("no\ncorrection", peaks(abl, "0"), COL["no"])]
    # stacked-dot plot: outcome is a small integer, so show every run as a dot stacked by value
    for i, (lab, vals, col) in enumerate(conds):
        for val, k in collections.Counter(vals).items():
            offs = (np.arange(k) - (k - 1) / 2) * 0.045
            ax[1].scatter(i + offs, [val] * k, s=22, color=col, alpha=0.8, edgecolor="white", linewidth=0.3)
        m, e = mse(vals); ax[1].errorbar(i, m, yerr=1.96 * e, fmt="o", color="k", ms=8, capsize=4, zorder=5)
    ax[1].set_xticks(range(3)); ax[1].set_xticklabels([c[0] for c in conds], fontsize=9)
    ax[1].set_yticks([0, 1, 2]); ax[1].set_ylabel("peaks colonized (per run; 20 runs each)")
    ax[1].set_ylim(-0.3, 2.4); pubfig.panel(ax[1], "B")
    # C: best attainable fitness per run; axis begins at 0.70 to make the cap legible
    def peakfit(folder, ecm):
        br, em = pergen(folder)
        return [max(mf for _, _, mf, _, _ in br[r]) for r in br if em[r] == ecm]
    fc = [("full-dict\ncorrection", peakfit("simthresh_0.80", "1"), COL["ecm"]),
          ("reduced-dict\ncorrection", peakfit("dict_ablation", "1"), COL["accent"]),
          ("no\ncorrection", peakfit("dict_ablation", "0"), COL["no"])]
    for i, (lab, v, col) in enumerate(fc):
        jit = np.random.default_rng(i + 10).normal(0, 0.05, len(v))
        ax[2].scatter(np.full(len(v), i) + jit, v, s=18, color=col, alpha=0.6, edgecolor="none")
        m, e = mse(v); ax[2].errorbar(i, m, yerr=1.96 * e, fmt="o", color="k", ms=8, capsize=4, zorder=5)
    ax[2].axhline(0.90, color=COL["gray"], ls=":", lw=1.1)
    ax[2].text(2.42, 0.903, "0.90 band", fontsize=8, color=COL["gray"], ha="right", va="bottom")
    ax[2].set_xticks(range(3)); ax[2].set_xticklabels([c[0] for c in fc], fontsize=9)
    ax[2].set_ylim(0.70, 1.01); ax[2].set_ylabel("best fitness reached (per run)")
    ax[2].text(0.02, 0.02, "axis begins at 0.70", transform=ax[2].transAxes, fontsize=7.5, color=COL["gray"])
    pubfig.panel(ax[2], "C")
    print("fig6_boundary ->", pubfig.finish(fig, os.path.join(OUT, "fig6_boundary.png")))


# ============================ SI: fitness-gated correction (mechanism test) ============================
def fig_gating():
    full = load("simthresh_0.80"); ab = load("gate_above"); be = load("gate_below")
    def pk(rows, ecm): return [float(r["final_peaks_colonized"]) for r in rows if r["use_ecm"] == ecm]
    conds = [("full\ncorrection", pk(full, "1"), COL["ecm"]),
             ("correct only\n≥0.90", pk(ab, "1"), COL["accent"]),
             ("correct only\n<0.90", pk(be, "1"), "#8856a7"),
             ("no\ncorrection", pk(full, "0"), COL["no"])]
    base = statistics.mean(pk(full, "0"))
    fig, axx = plt.subplots(figsize=(6.6, 4.2)); ax = axx
    for i, (lab, vals, col) in enumerate(conds):
        for val, k in collections.Counter(vals).items():
            offs = (np.arange(k) - (k - 1) / 2) * 0.05
            ax.scatter(i + offs, [val] * k, s=20, color=col, alpha=0.75, edgecolor="white", linewidth=0.3)
        m, e = mse(vals); ax.errorbar(i, m, yerr=1.96 * e, fmt="o", color="k", ms=8, capsize=4, zorder=5)
        d = m - base
        ax.text(i, 2.28, (f"+{d:.2f}" if d > 0 else f"{d:.2f}") + "\nvs none", ha="center", va="bottom",
                fontsize=8.5, color=col)
    ax.set_xticks(range(4)); ax.set_xticklabels([c[0] for c in conds], fontsize=9)
    ax.set_yticks([0, 1, 2]); ax.set_ylim(-0.3, 2.75)
    ax.set_ylabel("peaks colonized (per run; 20 runs each)")
    ax.set_title("Target attainment under fitness-gated correction")
    print("figS_gating ->", pubfig.finish(fig, os.path.join(OUT, "figS_gating.png")))


if __name__ == "__main__":
    fig_robustness(); fig_mechanism(); fig_boundary(); fig_gating()
