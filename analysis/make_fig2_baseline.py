"""Figure 2: single-peak baseline, regenerated with the current verified code (data/stage1_baseline,
from run_baseline_fig2.py). Panel A = mean fitness over generations at a representative multiplier
(correction climbs faster). Panel B = final mean fitness across the four multipliers with 95% CIs
(correction buffers against mutation; the conditions converge at low/moderate rates and diverge at
the highest). All values from raw CSV; carry-forward handles runs that stop early on convergence.
"""
import os, sys, csv, collections, statistics
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
ROOT = os.path.dirname(HERE)
import pubfig, matplotlib.pyplot as plt
pubfig.apply(); COL = pubfig.COL
CSV = os.path.join(ROOT, "data", "stage1_baseline", "stage1_per_generation.csv")
OUT = os.path.join(ROOT, "figures", "pub", "fig2_baseline.png")
REP_MULT = 1.0
MULTS = [0.25, 0.5, 1.0, 1.5]


def load():
    return list(csv.DictReader(open(CSV)))


def perrun(rows, sc, cond):
    """run_id -> {gen: mean_fitness} for one (multiplier, condition)."""
    d = collections.defaultdict(dict)
    for r in rows:
        if r["use_ecm"] == cond and abs(float(r["mutation_scalar"]) - sc) < 1e-9:
            d[r["run_id"]][int(r["generation"])] = float(r["mean_fitness"])
    return d


def cf(run, g):
    if g in run: return run[g]
    ks = [k for k in run if k <= g]
    return run[max(ks)] if ks else 0.0


def traj(rows, sc, cond):
    d = perrun(rows, sc, cond)
    gmax = max(max(v) for v in d.values())
    gs = list(range(0, gmax + 1))
    means, los, his = [], [], []
    for g in gs:
        vals = [cf(run, g) for run in d.values()]
        m = statistics.mean(vals); se = statistics.stdev(vals) / len(vals) ** 0.5
        means.append(m); los.append(m - 1.96 * se); his.append(m + 1.96 * se)
    return gs, means, los, his


def final(rows, sc, cond):
    d = perrun(rows, sc, cond)
    fin = [run[max(run)] for run in d.values()]
    return statistics.mean(fin), 1.96 * statistics.stdev(fin) / len(fin) ** 0.5


def main():
    rows = load()
    fig, ax = plt.subplots(1, 2, figsize=(9.4, 3.9))
    # Panel A: trajectory at the representative multiplier
    for cond, col, lab in [("1", COL["ecm"], "error correction"), ("0", COL["no"], "no correction")]:
        gs, m, lo, hi = traj(rows, REP_MULT, cond)
        ax[0].plot(gs, m, color=col, label=lab)
        ax[0].fill_between(gs, lo, hi, color=col, alpha=0.15, linewidth=0)
    ax[0].set_xlabel("generation"); ax[0].set_ylabel("mean fitness")
    ax[0].set_title(f"Faster climb with correction (multiplier {REP_MULT:g})")
    ax[0].set_ylim(0, 1); ax[0].legend(loc="lower right"); pubfig.panel(ax[0], "A")
    # Panel B: final fitness across multipliers
    for cond, col, lab, mk in [("1", COL["ecm"], "error correction", "o"),
                               ("0", COL["no"], "no correction", "s")]:
        ms = [final(rows, sc, cond) for sc in MULTS]
        ax[1].errorbar(MULTS, [m for m, _ in ms], yerr=[e for _, e in ms],
                       fmt=mk + "-", color=col, label=lab, capsize=3)
    ax[1].set_xlabel("mutation rate multiplier"); ax[1].set_ylabel("final mean fitness")
    ax[1].set_title("Correction buffers against mutation")
    ax[1].set_xticks(MULTS); ax[1].set_ylim(0, 1); ax[1].legend(loc="lower left"); pubfig.panel(ax[1], "B")
    print("fig2_baseline ->", pubfig.finish(fig, OUT))


if __name__ == "__main__":
    main()
