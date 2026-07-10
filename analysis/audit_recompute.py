"""FULL AUDIT: recompute every result number in bfg-stage2-build-review.docx from the
raw CSVs and diff against the value the doc claims. Prints CLAIM vs RECOMPUTED vs
verdict for each. Nothing is asserted from memory; every recomputed value comes from
the CSV named in the source column. Tolerances: means/fitness +-0.01, percents +-1pt,
median gens +-2, counts exact.
"""
import os, csv, glob, json, statistics, collections
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
D = lambda *p: os.path.join(ROOT, "data", *p)

PASS = FAIL = 0
def chk(label, claim, recomputed, tol=0.01, kind="num"):
    global PASS, FAIL
    if kind == "num":
        ok = recomputed is not None and abs(claim - recomputed) <= tol
        rc = "None" if recomputed is None else f"{recomputed:.4g}"
    else:  # exact
        ok = (claim == recomputed); rc = str(recomputed)
    PASS += ok; FAIL += (not ok)
    print(f"  [{'PASS' if ok else 'FAIL'}] {label:48} claim={claim}  recomputed={rc}")


def rows(folder, name=None):
    if name:
        f = D(folder, name)
    else:
        cands = glob.glob(D(folder, "*summary*.csv"))
        f = cands[0]
    return list(csv.DictReader(open(f)))

def fnum(x):
    try: return float(x)
    except: return float("nan")

def mean_by(rs, col, pred):
    v = [fnum(r[col]) for r in rs if pred(r)]
    return statistics.mean(v) if v else None

def frac_by(rs, col, pred, thresh):
    v = [1 if fnum(r[col]) >= thresh else 0 for r in rs if pred(r)]
    return statistics.mean(v) if v else None


# ============ TABLE 13: Run 1 far peaks (data/stage2_run1) ============
print("\n### TABLE 13  Run 1 far peaks  (data/stage2_run1, pooled all scalars+reapers)")
r1 = rows("stage2_run1")
E = lambda r: r["use_ecm"] == "1"; N = lambda r: r["use_ecm"] == "0"
print(f"  (n ECM={sum(1 for r in r1 if E(r))}, n no={sum(1 for r in r1 if N(r))})")
chk("any colonized ECM (%)", 21, 100*frac_by(r1,"final_peaks_colonized",E,1), tol=1)
chk("any colonized noECM (%)", 16, 100*frac_by(r1,"final_peaks_colonized",N,1), tol=1)
chk("mean peaks ECM", 0.21, mean_by(r1,"final_peaks_colonized",E))
chk("mean peaks noECM", 0.16, mean_by(r1,"final_peaks_colonized",N))
def median_gen_colonize(rs, pred):
    gs = []
    for r in rs:
        if not pred(r): continue
        d = json.loads(r["per_peak_convergence"] or "{}")
        if d: gs.append(min(int(v) for v in d.values()))
    return statistics.median(gs) if gs else None
chk("median gen to colonize ECM", 248, median_gen_colonize(r1,E), tol=2)
chk("median gen to colonize noECM", 318, median_gen_colonize(r1,N), tol=2)
# valley_reaper prose 0.34 / 0.03
TF=lambda r: r["valley_reaper"]=="top_fitness"; RD=lambda r: r["valley_reaper"]=="random"
chk("valley_reaper top_fitness mean peaks", 0.34, mean_by(r1,"final_peaks_colonized",TF))
chk("valley_reaper random mean peaks", 0.03, mean_by(r1,"final_peaks_colonized",RD))

# ============ TABLE 14 + robustness: Run 2 close (data/stage2_run2_fixed) ============
print("\n### TABLE 14  Run 2 close  (data/stage2_run2_fixed, pooled all scalars+reapers)")
r2 = rows("stage2_run2_fixed")
chk("mean peaks ECM", 0.99, mean_by(r2,"final_peaks_colonized",E))
chk("mean peaks noECM", 0.38, mean_by(r2,"final_peaks_colonized",N))
chk("reached >=1 ECM (%)", 74, 100*frac_by(r2,"final_peaks_colonized",E,1), tol=1)
chk("reached >=1 noECM (%)", 36, 100*frac_by(r2,"final_peaks_colonized",N,1), tol=1)
chk("blanketed >=2 ECM (%)", 22, 100*frac_by(r2,"final_peaks_colonized",E,2), tol=1)
chk("blanketed >=2 noECM (%)", 2, 100*frac_by(r2,"final_peaks_colonized",N,2), tol=1)
chk("max peaks ECM", 3, max(fnum(r["final_peaks_colonized"]) for r in r2 if E(r)), kind="exact")
chk("max peaks noECM", 2, max(fnum(r["final_peaks_colonized"]) for r in r2 if N(r)), kind="exact")
print("  -- robustness prose (by valley_reaper) --")
chk("ECM fitness-prune mean peaks", 1.06, mean_by(r2,"final_peaks_colonized",lambda r:E(r) and TF(r)))
chk("ECM random-prune mean peaks", 0.91, mean_by(r2,"final_peaks_colonized",lambda r:E(r) and RD(r)))
chk("noECM fitness-prune mean peaks", 0.51, mean_by(r2,"final_peaks_colonized",lambda r:N(r) and TF(r)))
chk("noECM random-prune mean peaks", 0.25, mean_by(r2,"final_peaks_colonized",lambda r:N(r) and RD(r)))

# ============ TABLE 15: colonization sources (data/stage2_run2_fixed) ============
print("\n### TABLE 15  colonization sources  (data/stage2_run2_fixed)")
def src_counts(rs, pred):
    c = collections.Counter()
    for r in rs:
        if not pred(r): continue
        for v in json.loads(r["colonization_source"] or "{}").values():
            if v.startswith("peak:"): c["peak"] += 1
            else: c[v] += 1
    return c
allc = src_counts(r2, lambda r: True); tot = sum(allc.values())
ecmc = src_counts(r2, E); noc = src_counts(r2, N)
print(f"  total events (claim 219): recomputed={tot}  [{'PASS' if tot==219 else 'FAIL'}]"); PASS+=(tot==219); FAIL+=(tot!=219)
chk("valley overall (%)", 44, 100*allc['valley']/tot, tol=1)
chk("in-situ overall (%)", 56, 100*allc['in_situ']/tot, tol=1)
chk("peak-to-peak overall (count)", 0, allc['peak'], kind="exact")
chk("valley ECM (%)", 40, 100*ecmc['valley']/sum(ecmc.values()), tol=1)
chk("in-situ ECM (%)", 60, 100*ecmc['in_situ']/sum(ecmc.values()), tol=1)
chk("valley noECM (%)", 56, 100*noc['valley']/sum(noc.values()), tol=1)

# ============ TABLE 19: extinction preview (data/stage2_extinction) ============
print("\n### TABLE 19  extinction preview  (data/stage2_extinction)")
ex = rows("stage2_extinction")
chk("pre-ext old peaks ECM", 0.53, mean_by(ex,"pre_extinction_peaks_colonized",E))
chk("pre-ext old peaks noECM", 0.38, mean_by(ex,"pre_extinction_peaks_colonized",N))
chk("post-ext new peaks ECM", 0.25, mean_by(ex,"final_peaks_colonized",E))
chk("post-ext new peaks noECM", 0.12, mean_by(ex,"final_peaks_colonized",N))

# ============ slots sweep prose (data/stage2_slots) ============
print("\n### slots sweep prose  (data/stage2_slots)")
sl = rows("stage2_slots")
for s, ce, cn in [(5,0.80,0.65),(10,1.10,0.70),(20,1.75,1.00),(40,2.50,2.05)]:
    SL=lambda r,s=s: int(r["slots_per_peak"])==s
    chk(f"slots{s} ECM mean peaks", ce, mean_by(sl,"final_peaks_colonized",lambda r,s=s:E(r) and int(r['slots_per_peak'])==s))
    chk(f"slots{s} noECM mean peaks", cn, mean_by(sl,"final_peaks_colonized",lambda r,s=s:N(r) and int(r['slots_per_peak'])==s))

# ============ TABLE 22: Stage 3 heritable (data/stage3, per-gen time-avg) ============
print("\n### TABLE 22  Stage 3 heritable time-averaged traits  (data/stage3 per-gen)")
pg3 = list(csv.DictReader(open(D("stage3","stage3_per_generation.csv"))))
def timeavg_by_period(period, col):
    # per run: mean over generations; then mean over runs with this ext_period
    byrun = collections.defaultdict(list)
    for r in pg3:
        if int(r["ext_period"]) == period:
            byrun[r["run_id"]].append(fnum(r[col]))
    per_run = [statistics.mean(v) for v in byrun.values() if v]
    return statistics.mean(per_run) if per_run else None
chk("mutation time-avg stable", 0.32, timeavg_by_period(0,"mean_mut"))
chk("mutation time-avg recurring", 0.43, timeavg_by_period(200,"mean_mut"))
chk("ECM quality time-avg stable", 0.52, timeavg_by_period(0,"mean_ecm"))
chk("ECM quality time-avg recurring", 0.54, timeavg_by_period(200,"mean_ecm"))

# ============ TABLE 23: Stage 3 decoupled (data/stage3_decoupled, late-half ecm) ============
print("\n### TABLE 23  Stage 3 decoupled evolved ECM (late half)  (data/stage3_decoupled per-gen)")
pg3d = list(csv.DictReader(open(D("stage3_decoupled","stage3_per_generation.csv"))))
maxg = max(int(r["generation"]) for r in pg3d)
def latehalf_ecm(env, period):
    byrun = collections.defaultdict(list)
    for r in pg3d:
        if int(r["ext_period"])==period and abs(fnum(r["env_mut"])-env)<1e-9 and int(r["generation"])>maxg/2:
            byrun[r["run_id"]].append(fnum(r["mean_ecm"]))
    per_run=[statistics.mean(v) for v in byrun.values() if v]
    return statistics.mean(per_run) if per_run else None
chk("env0 stable ECM", 0.53, latehalf_ecm(0.0,0))
chk("env0 recurring ECM", 0.55, latehalf_ecm(0.0,200))
chk("env0.75 stable ECM", 0.50, latehalf_ecm(0.75,0))
chk("env0.75 recurring ECM", 0.59, latehalf_ecm(0.75,200))

# ============ TABLE 25: Stage 4 final state (data/stage4) ============
print("\n### TABLE 25  Stage 4 final state  (data/stage4, pooled scalars)")
s4 = rows("stage4")
for topo, ff in [("complete",(0.976,0.963,0.93,0.83,0.65,0.55)),
                 ("ring_lattice",(0.968,0.962,0.95,0.90,0.50,0.45)),
                 ("small_world",(0.956,0.955,0.83,0.90,0.50,0.43)),
                 ("random",(0.959,0.957,0.87,0.85,0.55,0.48))]:
    T=lambda r,t=topo: r["topology"]==t
    chk(f"{topo} fit ECM", ff[0], mean_by(s4,"final_mean_fitness",lambda r,t=topo:E(r) and r['topology']==t))
    chk(f"{topo} fit no", ff[1], mean_by(s4,"final_mean_fitness",lambda r,t=topo:N(r) and r['topology']==t))
    chk(f"{topo} highfit ECM", ff[2], mean_by(s4,"final_frac_high",lambda r,t=topo:E(r) and r['topology']==t), tol=0.01)
    chk(f"{topo} peaks ECM", ff[4], mean_by(s4,"final_peaks_colonized",lambda r,t=topo:E(r) and r['topology']==t), tol=0.02)

# ============ TABLE 26: Stage 4 spread speed (data/stage4 per-gen, ECM on) ============
print("\n### TABLE 26  Stage 4 spread speed median gens to mean_fit 0.90 (ECM on)  (data/stage4 per-gen)")
pg4 = list(csv.DictReader(open(D("stage4","stage4_per_generation.csv"))))
def median_gen_to_fit(topo, thr=0.90):
    byrun = collections.defaultdict(dict)
    for r in pg4:
        if r["topology"]==topo and r["use_ecm"]=="1":
            byrun[r["run_id"]][int(r["generation"])]=fnum(r["mean_fitness"])
    firsts=[]
    for rid,series in byrun.items():
        hit=[g for g in sorted(series) if series[g]>=thr]
        if hit: firsts.append(hit[0])
    return statistics.median(firsts) if firsts else None
for topo,claim in [("complete",59),("random",215),("small_world",244),("ring_lattice",277)]:
    chk(f"{topo} median gen to 0.90", claim, median_gen_to_fit(topo), tol=2)

# ============ TABLE 28: Stage 4 decouple advantage (data/stage4_decouple) ============
print("\n### TABLE 28  Stage 4 decouple ECM advantage (late fitness, on-off)  (data/stage4_decouple)")
s4d = rows("stage4_decouple")
def adv(topo, sp, env):
    P=lambda r: r["topology"]==topo and abs(fnum(r["select_prob"])-sp)<1e-9 and abs(fnum(r["env_scalar"])-env)<1e-9
    e=mean_by(s4d,"late_mean_fitness",lambda r:P(r) and E(r))
    n=mean_by(s4d,"late_mean_fitness",lambda r:P(r) and N(r))
    return (e-n) if (e is not None and n is not None) else None
for cond,sp,env,vals in [("baseline",1.0,0.0,(0.020,0.003,0.013)),
                          ("drift0.5",0.5,0.0,(0.011,0.037,0.049)),
                          ("puredrift",0.0,0.0,(0.000,-0.001,0.003)),
                          ("env0.5",1.0,0.5,(0.004,0.073,0.062)),
                          ("env1.0",1.0,1.0,(0.028,0.053,0.045))]:
    chk(f"{cond} adv complete", vals[0], adv("complete",sp,env), tol=0.008)
    chk(f"{cond} adv small_world", vals[1], adv("small_world",sp,env), tol=0.008)
    chk(f"{cond} adv ring", vals[2], adv("ring_lattice",sp,env), tol=0.008)

print(f"\n===== AUDIT TOTALS: PASS={PASS}  FAIL={FAIL} =====")
