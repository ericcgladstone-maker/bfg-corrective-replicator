"""Stage 3 harness — heritable mutation rate and ECM quality, with vs without recurring
extinctions. Measures how the population-mean strategy (mut, ecm) evolves over time.

Local, resume-safe, multiprocessing, atomic writes, full manifest — same discipline as
run_stage2.py.

  caffeinate -i python3 analysis/run_stage3.py
"""

import argparse, base64, csv, gzip, hashlib, json, os, sys, time
from collections import defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
PROJECT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
import bfg_stage2 as s2

REPS = 20
MAX_GENS = 1000
EXT_PERIOD = 200          # recurring extinction every N generations (for the extinction arm)
ENV_MUTS = [0.0, 0.75]    # environmental mutation floor (decoupling knob): 0 = redundant with mut
K_PEAKS = 5
WORKERS = 8

PER_GEN_FIELDS = ["run_id", "ext_period", "env_mut", "rep", "generation", "epoch", "mean_fitness",
                  "max_fitness", "peaks_colonized", "mean_mut", "mean_ecm", "n"]
SUMMARY_FIELDS = ["run_id", "ext_period", "env_mut", "rep", "seed", "generations_run",
                  "final_mean_mut", "final_mean_ecm", "extinctions"]


def load_real_data():
    nb = json.load(open(os.path.join(HERE, "BFG_Simulation_v6.ipynb")))
    src = "".join(nb["cells"][2]["source"])
    ns = {"base64": base64, "gzip": gzip, "defaultdict": defaultdict}
    try:
        exec(src, ns)
    except Exception:
        pass
    return ns["WORD_SET"], ns["TG_IDX"], ns["SEEDS"], ns["TARGETS_RAW"]


def build_peak_sets(targets, k, n_clusters):
    """n_clusters reachable close-clusters around the easiest anchor (target 0): cluster c is
    the c-th block of k nearest neighbours, so they share a reachable region but are distinct."""
    nbrs = [0] + sorted((i for i in range(len(targets)) if i != 0),
                        key=lambda i: s2.levenshtein(targets[0], targets[i]))
    sets = []
    for c in range(n_clusters):
        idx = sorted(nbrs[c * k:(c + 1) * k])
        sets.append((idx, [targets[i] for i in idx]))
    return sets


_G = {}


def _init(word_set, tg_idx, seeds, cluster_strs, max_gens):
    _G["ws"], _G["tg"], _G["seeds"] = word_set, tg_idx, seeds
    _G["clusters"] = [s2.make_peaks(cs) for cs in cluster_strs]
    _G["max_gens"] = max_gens


def run_id_of(job):
    ext_period, env, rep = job
    return f"ext{ext_period}_env{env}_{rep:02d}"


def _run(job):
    ext_period, env, rep = job
    run_id = run_id_of(job)
    seed = int(hashlib.md5(run_id.encode()).hexdigest()[:8], 16)
    # extinction arm rotates through all clusters; no-extinction arm stays on cluster 0
    peak_sets = _G["clusters"] if ext_period else _G["clusters"][:1]
    cfg = s2.Stage3Config(max_generations=_G["max_gens"], extinction_period=ext_period,
                          env_mut=env, seed=seed)
    out = s2.run_stage3(cfg, peak_sets, _G["seeds"], _G["ws"], _G["tg"], run_id=run_id)
    out["seed"] = seed
    out["ext_period"] = ext_period
    out["env_mut"] = env
    out["rep"] = rep
    return out


def _append(path, fields, rows):
    new = not os.path.exists(path)
    with open(path, "a", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        if new:
            w.writeheader()
        for r in rows:
            w.writerow(r)
        f.flush()
        os.fsync(f.fileno())


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=os.path.join(PROJECT, "data", "stage3"))
    ap.add_argument("--reps", type=int, default=REPS)
    ap.add_argument("--gens", type=int, default=MAX_GENS)
    ap.add_argument("--smoke", action="store_true")
    args = ap.parse_args()
    os.makedirs(args.out, exist_ok=True)
    per_gen_csv = os.path.join(args.out, "stage3_per_generation.csv")
    summary_csv = os.path.join(args.out, "stage3_summary.csv")

    word_set, tg_idx, seeds, targets = load_real_data()
    k = 3 if args.smoke else K_PEAKS
    n_clusters = max(2, (args.gens // EXT_PERIOD) + 1)
    peak_sets = build_peak_sets(targets, k, n_clusters)
    cluster_idx = [s[0] for s in peak_sets]
    cluster_strs = [s[1] for s in peak_sets]
    gens = 80 if args.smoke else args.gens
    reps = 1 if args.smoke else args.reps

    jobs = [(ep, env, rep) for rep in range(reps) for ep in (0, EXT_PERIOD) for env in ENV_MUTS]

    code_hash = hashlib.md5(open(os.path.join(HERE, "bfg_stage2.py"), "rb").read()).hexdigest()
    json.dump({"spec": {"ext_periods": [0, EXT_PERIOD], "env_muts": ENV_MUTS,
                        "n_reps": reps, "max_generations": gens, "k_peaks": k,
                        "extinction_period": EXT_PERIOD, "n_clusters": n_clusters,
                        "total_runs": len(jobs)},
               "cluster_indices": cluster_idx, "clusters": cluster_strs, "seeds": seeds,
               "dictionary_words": len(word_set), "bfg_stage2_md5": code_hash,
               "note": "heritable mut + ecm; extinction arm rotates peak clusters every period"},
              open(os.path.join(args.out, "manifest.json"), "w"), indent=2)

    completed = set()
    if os.path.exists(summary_csv):
        with open(summary_csv) as f:
            completed = {r["run_id"] for r in csv.DictReader(f)}
    if os.path.exists(per_gen_csv) and completed:
        with open(per_gen_csv) as f:
            rows = [r for r in csv.DictReader(f) if r["run_id"] in completed]
        with open(per_gen_csv, "w", newline="") as f:
            w = csv.DictWriter(f, fieldnames=PER_GEN_FIELDS)
            w.writeheader()
            w.writerows(rows)

    remaining = [j for j in jobs if run_id_of(j) not in completed]
    print(f"[{time.strftime('%H:%M:%S')}] {len(completed)} done, {len(remaining)} remaining "
          f"of {len(jobs)} | clusters={cluster_idx} | out={args.out}", flush=True)

    import multiprocessing as mp
    t0 = time.time(); done = len(completed)
    with mp.get_context("spawn").Pool(WORKERS, initializer=_init,
                                      initargs=(word_set, tg_idx, seeds, cluster_strs, gens)) as pool:
        for out in pool.imap_unordered(_run, remaining):
            rid = out["run_id"]; sm = out["summary"]
            for r in out["rows"]:
                r["ext_period"] = out["ext_period"]; r["env_mut"] = out["env_mut"]; r["rep"] = out["rep"]
            _append(per_gen_csv, PER_GEN_FIELDS, out["rows"])
            _append(summary_csv, SUMMARY_FIELDS, [{
                "run_id": rid, "ext_period": out["ext_period"], "env_mut": out["env_mut"],
                "rep": out["rep"],
                "seed": out["seed"], "generations_run": sm["generations_run"],
                "final_mean_mut": sm["final_mean_mut"], "final_mean_ecm": sm["final_mean_ecm"],
                "extinctions": json.dumps(sm["extinctions"])}])
            done += 1
            el = time.time() - t0
            eta = (len(jobs) - done) / ((done - len(completed)) / el) / 60 if el > 0 and done > len(completed) else 0
            print(f"[{time.strftime('%H:%M:%S')}] {done}/{len(jobs)} {rid} "
                  f"final_ecm={sm['final_mean_ecm']} final_mut={sm['final_mean_mut']} ETA~{eta:.0f}m", flush=True)
    print(f"[{time.strftime('%H:%M:%S')}] DONE. {done}/{len(jobs)}. {time.time()-t0:.0f}s -> {args.out}", flush=True)


if __name__ == "__main__":
    main()
