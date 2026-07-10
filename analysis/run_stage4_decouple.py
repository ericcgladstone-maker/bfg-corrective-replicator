"""Stage 4 DECOUPLING probe — does error correction become non-redundant when we decouple it
from selection-at-reception? Two knobs, both crossed with ECM on/off and topology:

  knob A  select_prob : P(node adopts the FITTEST copy it sees); 1-p => adopt a random transmitted
                        copy (fitness-blind drift). Removes selection's FILTER.
  knob B  env_scalar  : environmental transmission load applied to the adopted copy AFTER
                        selection (selection cannot filter it; only correction cleans it). The
                        faithful network analogue of Stage 3's env_mut.

Question: does weakening the selection filter (A) or adding an uncorrectable-by-selection load (B)
give correction a non-redundant role, widening the ECM advantage in maintained (late-window) fitness?

Same discipline as run_stage4.py: local, resume-safe, multiprocessing, atomic writes, manifest.

  caffeinate -i python3 analysis/run_stage4_decouple.py
"""

import argparse, base64, csv, gzip, hashlib, json, os, random, sys, time
from collections import defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
PROJECT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
import bfg_stage2 as s2
import bfg_stage4 as s4

TOPOLOGIES = ["complete", "small_world", "ring_lattice"]   # well-mixed / local+long / local-only
# (select_prob, env_scalar): baseline, drift arm (env=0), load arm (select_prob=1)
CONDITIONS = [(1.0, 0.0), (0.5, 0.0), (0.0, 0.0), (1.0, 0.5), (1.0, 1.0)]
ECM = [True, False]
REPS = 20
N_NODES = 100
GENS = 300
SCALAR = 1.0
K_PEAKS = 5
DEGREE = 6
REWIRE_P = 0.1
LATE_WINDOW = 100
WORKERS = 8

PER_GEN_FIELDS = ["run_id", "topology", "select_prob", "env_scalar", "use_ecm", "rep", "generation",
                  "mean_fitness", "max_fitness", "n_full_fit", "frac_high", "peaks_colonized"]
SUMMARY_FIELDS = ["run_id", "topology", "select_prob", "env_scalar", "use_ecm", "rep", "seed",
                  "generations_run", "final_mean_fitness", "late_mean_fitness", "late_frac_high",
                  "final_peaks_colonized"]


def load_real_data():
    nb = json.load(open(os.path.join(HERE, "BFG_Simulation_v6.ipynb")))
    src = "".join(nb["cells"][2]["source"])
    ns = {"base64": base64, "gzip": gzip, "defaultdict": defaultdict}
    try:
        exec(src, ns)
    except Exception:
        pass
    return ns["WORD_SET"], ns["TG_IDX"], ns["SEEDS"], ns["TARGETS_RAW"]


_G = {}


def _init(word_set, tg_idx, seeds, peak_strs, n_nodes, gens):
    _G["ws"], _G["tg"], _G["seeds"] = word_set, tg_idx, seeds
    _G["peaks"] = s2.make_peaks(peak_strs)
    _G["n"], _G["gens"] = n_nodes, gens


def run_id_of(job):
    topo, sp, env, ecm, rep = job
    return f"{topo}_sp{sp}_env{env}_ecm{int(ecm)}_{rep:02d}"


def _run(job):
    topo, sp, env, ecm, rep = job
    run_id = run_id_of(job)
    seed = int(hashlib.md5(run_id.encode()).hexdigest()[:8], 16)
    graph = s4.make_graph(topo, _G["n"], random.Random(seed), k=DEGREE, rewire_p=REWIRE_P)
    cfg = s4.Stage4Config(n_nodes=_G["n"], mutation_scalar=SCALAR, use_ecm=ecm,
                          max_generations=_G["gens"], select_prob=sp, env_scalar=env,
                          late_window=LATE_WINDOW, seed=seed)
    out = s4.run_stage4(cfg, _G["peaks"], _G["seeds"], _G["ws"], _G["tg"], graph, run_id=run_id)
    out.update({"seed": seed, "topology": topo, "select_prob": sp, "env_scalar": env,
                "use_ecm": ecm, "rep": rep})
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
    ap.add_argument("--out", default=os.path.join(PROJECT, "data", "stage4_decouple"))
    ap.add_argument("--reps", type=int, default=REPS)
    ap.add_argument("--gens", type=int, default=GENS)
    ap.add_argument("--n", type=int, default=N_NODES)
    ap.add_argument("--smoke", action="store_true")
    args = ap.parse_args()
    os.makedirs(args.out, exist_ok=True)
    per_gen_csv = os.path.join(args.out, "decouple_per_generation.csv")
    summary_csv = os.path.join(args.out, "decouple_summary.csv")

    word_set, tg_idx, seeds, targets = load_real_data()
    nbrs = [0] + sorted((i for i in range(len(targets)) if i != 0),
                        key=lambda i: s2.levenshtein(targets[0], targets[i]))
    peak_idx = sorted(nbrs[:K_PEAKS])
    peak_strs = [targets[i] for i in peak_idx]
    gens = 60 if args.smoke else args.gens
    n = 40 if args.smoke else args.n
    reps = 1 if args.smoke else args.reps
    topos = ["complete", "small_world"] if args.smoke else TOPOLOGIES

    jobs = [(t, sp, env, e, rep) for rep in range(reps) for t in topos
            for (sp, env) in CONDITIONS for e in ECM]

    code_hash = hashlib.md5(open(os.path.join(HERE, "bfg_stage4.py"), "rb").read()).hexdigest()
    json.dump({"spec": {"topologies": topos, "conditions_select_env": CONDITIONS, "ecm": ECM,
                        "n_reps": reps, "n_nodes": n, "max_generations": gens, "scalar": SCALAR,
                        "degree": DEGREE, "rewire_p": REWIRE_P, "k_peaks": K_PEAKS,
                        "late_window": LATE_WINDOW, "total_runs": len(jobs)},
               "peak_indices": peak_idx, "peaks": peak_strs, "seeds": seeds,
               "dictionary_words": len(word_set), "bfg_stage4_md5": code_hash,
               "note": "decoupling probe: knob A select_prob (drift), knob B env_scalar (post-"
                       "selection load only correction cleans); does either make ECM non-redundant"},
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
          f"of {len(jobs)} | peaks={peak_idx} | N={n} | topos={topos} | out={args.out}", flush=True)

    import multiprocessing as mp
    t0 = time.time(); done = len(completed)
    with mp.get_context("spawn").Pool(WORKERS, initializer=_init,
                                      initargs=(word_set, tg_idx, seeds, peak_strs, n, gens)) as pool:
        for out in pool.imap_unordered(_run, remaining):
            rid = out["run_id"]; sm = out["summary"]
            for r in out["rows"]:
                r["topology"] = out["topology"]; r["select_prob"] = out["select_prob"]
                r["env_scalar"] = out["env_scalar"]; r["use_ecm"] = int(out["use_ecm"]); r["rep"] = out["rep"]
            _append(per_gen_csv, PER_GEN_FIELDS, out["rows"])
            _append(summary_csv, SUMMARY_FIELDS, [{
                "run_id": rid, "topology": out["topology"], "select_prob": out["select_prob"],
                "env_scalar": out["env_scalar"], "use_ecm": int(out["use_ecm"]), "rep": out["rep"],
                "seed": out["seed"], "generations_run": sm["generations_run"],
                "final_mean_fitness": sm["final_mean_fitness"], "late_mean_fitness": sm["late_mean_fitness"],
                "late_frac_high": sm["late_frac_high"], "final_peaks_colonized": sm["final_peaks_colonized"]}])
            done += 1
            el = time.time() - t0
            eta = (len(jobs) - done) / ((done - len(completed)) / el) / 60 if el > 0 and done > len(completed) else 0
            print(f"[{time.strftime('%H:%M:%S')}] {done}/{len(jobs)} {rid} "
                  f"late_mf={sm['late_mean_fitness']} ETA~{eta:.0f}m", flush=True)
    print(f"[{time.strftime('%H:%M:%S')}] DONE. {done}/{len(jobs)}. {time.time()-t0:.0f}s -> {args.out}", flush=True)


if __name__ == "__main__":
    main()
