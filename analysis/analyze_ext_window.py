"""Widened-window extinction analysis: does the recovery advantage keep growing past
the 250-generation cutoff? Fires at gen 250, recovery window 750 (run to gen 1000).
Reports the post-extinction trajectory (mean new peaks colonized vs gens-since-firing)
for ECM vs no-ECM, and recovery speed (gens to first new colonization). All from CSV.
Writes figures/stage2_ext_window.png.
"""
import os, csv, collections, statistics
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PG = os.path.join(ROOT, "data", "stage2_ext_window", "stage2_per_generation.csv")
G = 250


def main():
    byrun = collections.defaultdict(dict); ecm = {}
    for r in csv.DictReader(open(PG)):
        byrun[r["run_id"]][int(r["generation"])] = int(r["peaks_colonized"])
        ecm[r["run_id"]] = int(r["use_ecm"])
    n1 = sum(1 for v in ecm.values() if v == 1)
    print(f"runs: {len(ecm)} ({n1} ECM / {len(ecm)-n1} no)  firing gen {G}, recovery window 750")

    def mean_at(g, e):
        vs = [byrun[r].get(g, 0) for r in ecm if ecm[r] == e]
        return statistics.mean(vs) if vs else float("nan")

    xs = list(range(G, 1000, 50)) + [999]
    print(f"\n{'sinceFire':>9} {'ECM':>6} {'noECM':>6} {'gap':>6}")
    traj = []
    for g in xs:
        e, n = mean_at(g, 1), mean_at(g, 0)
        traj.append((g - G, e, n))
        print(f"{g-G:>9} {e:>6.2f} {n:>6.2f} {e-n:>6.2f}")

    print("\nrecovery speed (gens after firing to first new colonization), among recolonizers:")
    for e, lab in [(1, "ECM"), (0, "noECM")]:
        firsts = []
        for r in ecm:
            if ecm[r] != e:
                continue
            hit = [g for g in sorted(byrun[r]) if g >= G and byrun[r][g] >= 1]
            if hit:
                firsts.append(hit[0] - G)
        if firsts:
            print(f"  {lab}: recolonized {len(firsts)}  median {statistics.median(firsts):.0f}  mean {statistics.mean(firsts):.0f}")
        else:
            print(f"  {lab}: none recolonized")

    try:
        import matplotlib; matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        x = [t[0] for t in traj]
        plt.figure(figsize=(7, 4.5))
        plt.plot(x, [t[1] for t in traj], "o-", label="error correction", color="#1f77b4")
        plt.plot(x, [t[2] for t in traj], "s--", label="no correction", color="#d62728")
        plt.axvline(250, color="gray", ls=":", lw=1, label="old 250-gen cutoff")
        plt.xlabel("generations after extinction (fired at gen 250)")
        plt.ylabel("mean new peaks recolonized")
        plt.title("Recovery with a widened 750-generation window")
        plt.legend(); plt.grid(alpha=.3); plt.tight_layout()
        out = os.path.join(ROOT, "figures", "stage2_ext_window.png")
        plt.savefig(out, dpi=140); print(f"\nfigure -> {os.path.relpath(out, ROOT)}")
    except Exception as e:
        print(f"(figure skipped: {e})")


if __name__ == "__main__":
    main()
