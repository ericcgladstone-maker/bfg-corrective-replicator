"""Confirmatory sensitivity check: does the mutation-character-pool difference between
the Python reimplementation and the original Java change the headline multi-peak result?

Our Python draws substitution/insertion characters uniformly from a 28-character pool
(a-z, hyphen, apostrophe). The original Java drew from a 54-character pool (A-Z, a-z,
hyphen, apostrophe); because all text is lowercased for scoring and correction, its
effective per-character distribution gives each lowercase letter weight 2/54 and each
punctuation mark 1/54 (letters ~2x as likely as punctuation).

This script runs the headline close 5-peak design under BOTH pools with IDENTICAL seeds,
so the only difference between the two arms is VALID_CHARS. It writes every per-run result
and a manifest (seeds, peak indices, both pools, model-code MD5) to disk, then prints the
comparison. Same integrity discipline as run_stage2.py: every number comes from an actual
run and lands on disk; the run is reproducible from the manifest.

Usage:  python3 analysis/pool_sensitivity.py
"""
import sys, os, csv, json, hashlib, statistics as st
from multiprocessing import Pool

HERE = os.path.dirname(os.path.abspath(__file__))
PROJECT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
import bfg_stage2 as s2
import run_stage2 as R

# --- headline close 5-peak design (matches run_stage2 locked spec) ---
SCALARS = [0.5, 1.0]          # headline pooled scalars
REPS = 20
VR = "top_fitness"            # fitness pruning (headline)
VCAP = 200
SLOTS = 10
MAXG = 500
K_PEAKS = 5
WORKERS = 10

POOLS = {
    "python_28_uniform": list("abcdefghijklmnopqrstuvwxyz-'"),
    "java_54_effective": list("abcdefghijklmnopqrstuvwxyz" * 2 + "-'"),
}
OUT = os.path.join(PROJECT, "data", "pool_sensitivity")

_G = {}
def _init():
    ws, tg, seeds, targets = R.load_real_data()
    peak_idx = R.select_peaks_close(targets, K_PEAKS)
    _G.update(ws=ws, tg=tg, seeds=seeds,
              peaks=s2.make_peaks([targets[i] for i in peak_idx]),
              peak_idx=peak_idx, peak_strs=[targets[i] for i in peak_idx])

def _work(job):
    pool_name, valid_chars, sc, ecm, rep = job
    s2.VALID_CHARS = valid_chars                      # the ONLY thing that varies between arms
    run_id = f"s{sc}_ecm{int(ecm)}_{VR}_vc{VCAP}_sl{SLOTS}_{rep:02d}"
    seed = int(hashlib.md5(run_id.encode()).hexdigest()[:8], 16)
    cfg = s2.Stage2Config(
        n_peaks=K_PEAKS, slots_per_peak=SLOTS, valley_capacity=VCAP, valley_reaper=VR,
        displacement=R.DISPLACEMENT, fitness_rule=R.FITNESS_RULE, max_generations=MAXG,
        mutation_scalar=sc, use_ecm=ecm, seed=seed, stop_on_blanket=True, no_progress_patience=0)
    out = s2.run_stage2(cfg, _G["peaks"], _G["seeds"], _G["ws"], _G["tg"], run_id=run_id)
    return {"pool": pool_name, "mutation_scalar": sc, "use_ecm": ecm, "rep": rep,
            "seed": seed, "run_id": run_id,
            "final_peaks_colonized": out["summary"]["final_peaks_colonized"]}

def summ(v):
    return st.mean(v), (st.pstdev(v) / len(v) ** 0.5 if len(v) > 1 else 0.0)

if __name__ == "__main__":
    os.makedirs(OUT, exist_ok=True)
    _init()
    code_hash = hashlib.md5(open(os.path.join(HERE, "bfg_stage2.py"), "rb").read()).hexdigest()
    jobs = [(name, vc, sc, ecm, rep)
            for name, vc in POOLS.items()
            for sc in SCALARS for ecm in (True, False) for rep in range(REPS)]

    with Pool(processes=WORKERS, initializer=_init) as p:
        results = p.map(_work, jobs, chunksize=1)

    # ---- persist per-run rows ----
    runs_csv = os.path.join(OUT, "pool_sensitivity_runs.csv")
    fields = ["pool", "mutation_scalar", "use_ecm", "rep", "seed", "run_id", "final_peaks_colonized"]
    with open(runs_csv, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields); w.writeheader()
        for r in sorted(results, key=lambda x: (x["pool"], x["mutation_scalar"], x["use_ecm"], x["rep"])):
            w.writerow(r)

    # ---- aggregate ----
    agg = {name: {True: [], False: []} for name in POOLS}
    for r in results:
        agg[r["pool"]][r["use_ecm"]].append(r["final_peaks_colonized"])
    report = {}
    for name in POOLS:
        me, see = summ(agg[name][True]); mn, sen = summ(agg[name][False])
        report[name] = {
            "ecm_mean": me, "ecm_se": see, "ecm_reach1_pct": 100 * sum(x >= 1 for x in agg[name][True]) / len(agg[name][True]),
            "noecm_mean": mn, "noecm_se": sen, "noecm_reach1_pct": 100 * sum(x >= 1 for x in agg[name][False]) / len(agg[name][False]),
            "advantage_ratio": me / mn if mn else None, "n_per_condition": len(agg[name][True])}

    # ---- manifest ----
    manifest = {
        "purpose": "mutation-pool sensitivity A/B: python 28-char uniform vs java 54-char effective, identical seeds",
        "design": {"peaks": "close", "k_peaks": K_PEAKS, "scalars": SCALARS, "reps": REPS,
                   "valley_reaper": VR, "valley_capacity": VCAP, "slots_per_peak": SLOTS,
                   "max_generations": MAXG, "exit_fitness": 0.99999,
                   "similarity_threshold": s2.SIMILARITY_THRESHOLD, "stop_on_blanket": True},
        "pools": {k: "".join(v) for k, v in POOLS.items()},
        "peak_indices": _G["peak_idx"], "peaks": _G["peak_strs"], "seeds": _G["seeds"],
        "bfg_stage2_md5": code_hash, "n_per_condition": len(SCALARS) * REPS,
        "total_runs": len(jobs), "data_source": "BFG_Simulation_v6.ipynb (canonical dict/targets/seeds)",
        "result": report,
    }
    json.dump(manifest, open(os.path.join(OUT, "manifest.json"), "w"), indent=2)

    # ---- print ----
    print(f"peaks (close 5): idx={_G['peak_idx']}")
    print(f"design: scalars={SCALARS} pooled, reps={REPS}, reaper={VR}, slots={SLOTS}, vcap={VCAP}, maxg={MAXG}")
    print(f"n per condition = {len(SCALARS) * REPS} runs   |   model md5={code_hash}")
    print(f"wrote: {runs_csv}\n       {os.path.join(OUT, 'manifest.json')}\n")
    for name in POOLS:
        r = report[name]
        print(f"[{name}]")
        print(f"   ECM   : mean peaks = {r['ecm_mean']:.3f} +- {r['ecm_se']:.3f}   reach>=1: {r['ecm_reach1_pct']:.0f}%")
        print(f"   no-ECM: mean peaks = {r['noecm_mean']:.3f} +- {r['noecm_se']:.3f}   reach>=1: {r['noecm_reach1_pct']:.0f}%")
        print(f"   ECM advantage: {r['advantage_ratio']:.2f}x\n")
    b, j = report["python_28_uniform"], report["java_54_effective"]
    print("=== SIDE BY SIDE ===")
    print(f"ECM   mean peaks : python28={b['ecm_mean']:.3f}   java54={j['ecm_mean']:.3f}   diff={j['ecm_mean']-b['ecm_mean']:+.3f}")
    print(f"noECM mean peaks : python28={b['noecm_mean']:.3f}   java54={j['noecm_mean']:.3f}   diff={j['noecm_mean']-b['noecm_mean']:+.3f}")
    print("published headline for reference: ECM ~0.90, noECM ~0.38 (320 runs/cond, pooled run1+run2)")
    print("\nDONE")
