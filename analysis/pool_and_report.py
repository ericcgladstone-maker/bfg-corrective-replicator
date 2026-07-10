"""Pool the old-code and current-code (_v2) draws for each headline dataset (the two are
proven logically identical by the seed-match test, so pooling is valid) and report means
with standard errors on ~2x the runs. Prints the pooled values matching each doc table so
the tables can be repointed. Skips a dataset if its _v2 folder is not present yet.
"""
import os, csv, glob, json, statistics, collections
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
D = lambda *p: os.path.join(ROOT, "data", *p)
E = lambda r: r.get("use_ecm") == "1"; N = lambda r: r.get("use_ecm") == "0"

def load(folder):
    f = glob.glob(D(folder, "*summary*.csv"))
    return list(csv.DictReader(open(f[0]))) if f else None

def pool(a, b):
    return (a or []) + (b or [])

def mse(rs, pred, col="final_peaks_colonized"):
    v = [float(r[col]) for r in rs if pred(r)]
    if not v: return None
    m = statistics.mean(v); se = statistics.stdev(v)/len(v)**0.5 if len(v) > 1 else 0
    return m, se, len(v)

def frac(rs, pred, t, col="final_peaks_colonized"):
    v = [1 if float(r[col]) >= t else 0 for r in rs if pred(r)]
    return 100*statistics.mean(v) if v else None

def line(lbl, r):
    print(f"  {lbl:34} {r[0]:.2f} +- {r[1]:.2f}  (n{r[2]})" if r else f"  {lbl:34} (no data)")

def sect(title): print(f"\n### {title}")

# ---- run1 far ----
o, n = load("stage2_run1"), load("stage2_run1_v2")
if n:
    sect("Run 1 far  (Table 13) pooled")
    p = pool(o, n)
    line("mean peaks ECM", mse(p, E)); line("mean peaks noECM", mse(p, N))
    print(f"  any colonized ECM {frac(p,E,1):.0f}%  noECM {frac(p,N,1):.0f}%")
    TF = lambda r: r["valley_reaper"]=="top_fitness"; RD = lambda r: r["valley_reaper"]=="random"
    line("top_fitness mean peaks", mse(p, TF)); line("random mean peaks", mse(p, RD))

# ---- run2 close ----
o, n = load("stage2_run2_fixed"), load("stage2_run2_v2")
if n:
    sect("Run 2 close  (Table 14/15) pooled")
    p = pool(o, n)
    line("mean peaks ECM", mse(p, E)); line("mean peaks noECM", mse(p, N))
    print(f"  reached>=1 ECM {frac(p,E,1):.0f}%  noECM {frac(p,N,1):.0f}%")
    print(f"  blanket>=2 ECM {frac(p,E,2):.0f}%  noECM {frac(p,N,2):.0f}%")
    print(f"  max peaks ECM {max(float(r['final_peaks_colonized']) for r in p if E(r)):.0f}  noECM {max(float(r['final_peaks_colonized']) for r in p if N(r)):.0f}")
    TF = lambda r: r["valley_reaper"]=="top_fitness"; RD = lambda r: r["valley_reaper"]=="random"
    line("ECM fitness-prune", mse(p, lambda r: E(r) and TF(r))); line("ECM random-prune", mse(p, lambda r: E(r) and RD(r)))
    line("noECM fitness-prune", mse(p, lambda r: N(r) and TF(r))); line("noECM random-prune", mse(p, lambda r: N(r) and RD(r)))
    # sources
    def src(rs, pred):
        c = collections.Counter()
        for r in rs:
            if not pred(r): continue
            for v in json.loads(r["colonization_source"] or "{}").values():
                c["peak" if v.startswith("peak:") else v] += 1
        return c
    c = src(p, lambda r: True); t = sum(c.values())
    print(f"  sources total={t}: valley {100*c['valley']/t:.0f}%  in_situ {100*c['in_situ']/t:.0f}%  peak {c['peak']}")
    ce, cn = src(p, E), src(p, N)
    print(f"  ECM valley/in_situ {100*ce['valley']/sum(ce.values()):.0f}/{100*ce['in_situ']/sum(ce.values()):.0f}  noECM {100*cn['valley']/sum(cn.values()):.0f}/{100*cn['in_situ']/sum(cn.values()):.0f}")

# ---- extinction ----
o, n = load("stage2_extinction"), load("stage2_extinction_v2")
if n:
    sect("Extinction preview  (Table 19) pooled")
    p = pool(o, n)
    line("pre-ext ECM", mse(p, E, "pre_extinction_peaks_colonized")); line("pre-ext noECM", mse(p, N, "pre_extinction_peaks_colonized"))
    line("post-ext ECM", mse(p, E)); line("post-ext noECM", mse(p, N))

# ---- slots ----
o, n = load("stage2_slots"), load("stage2_slots_v2")
if n:
    sect("Slots sweep pooled")
    p = pool(o, n)
    for s in (5, 10, 20, 40):
        line(f"slots{s} ECM", mse(p, lambda r, s=s: E(r) and int(r["slots_per_peak"])==s))
        line(f"slots{s} noECM", mse(p, lambda r, s=s: N(r) and int(r["slots_per_peak"])==s))

# ---- toy 4-peak (Table 10) -- current only ----
n = load("stage2_toy4peak")
if n:
    sect("Toy 4-peak pruning test  (Table 10) current")
    TF = lambda r: r["valley_reaper"]=="top_fitness"; RD = lambda r: r["valley_reaper"]=="random"
    line("top_fitness mean peaks (of 4)", mse(n, TF)); line("random mean peaks (of 4)", mse(n, RD))
    for lbl, pred in [("top_fitness", TF), ("random", RD)]:
        tb = [float(r["time_to_blanket"]) for r in n if pred(r) and r["time_to_blanket"] not in ("", "None")]
        print(f"  {lbl} time_to_blanket median: {statistics.median(tb):.0f}" if tb else f"  {lbl} never blanketed")

# ---- stage3 heritable (Table 22) time-avg pooled ----
def pg(folder):
    f = glob.glob(D(folder, "*per_generation*.csv"))
    return list(csv.DictReader(open(f[0]))) if f else None
o, n = pg("stage3"), pg("stage3_v2")
if n:
    sect("Stage 3 heritable time-averaged  (Table 22) pooled")
    allp = (o or []) + n
    def tavg(period, col):
        byrun = collections.defaultdict(list)
        for r in allp:
            if int(r["ext_period"]) == period: byrun[r["run_id"]].append(float(r[col]))
        pr = [statistics.mean(v) for v in byrun.values() if v]
        return statistics.mean(pr) if pr else None
    print(f"  mutation stable {tavg(0,'mean_mut'):.2f}  recurring {tavg(200,'mean_mut'):.2f}")
    print(f"  ECM stable {tavg(0,'mean_ecm'):.2f}  recurring {tavg(200,'mean_ecm'):.2f}")

# ---- stage4 final + spread (Table 25/26) pooled ----
o, n = load("stage4"), load("stage4_v2")
if n:
    sect("Stage 4 final state  (Table 25) pooled")
    p = pool(o, n)
    for topo in ("complete", "ring_lattice", "small_world", "random"):
        T = lambda r, t=topo: r["topology"] == t
        fe = mse(p, lambda r, t=topo: E(r) and r["topology"]==t, "final_mean_fitness")
        fn = mse(p, lambda r, t=topo: N(r) and r["topology"]==t, "final_mean_fitness")
        print(f"  {topo:13} fit ECM {fe[0]:.3f}  no {fn[0]:.3f}")

print("\n(pooling uses old + _v2; both proven identical by seed-match, so this is 2x runs)")
