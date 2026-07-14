"""Local, resume-safe, multiprocessing harness for the Stage 2 crossing.

Design requirements (Eric's):
  - consistent saving      : every completed run is appended (per-generation rows +
                             one summary row) with flush+fsync (durable).
  - no hallucinations      : every number comes from an actual run and lands on disk;
                             a manifest records the exact config, peaks, seeds, and a
                             hash of bfg_stage2.py, so any run is reproducible.
  - full transparency      : plain CSV (per-gen + summary) for human eyes, JSON manifest.
  - shutdown-resistant     : on restart, completed runs (those with a summary row) are
                             skipped; any partial per-gen rows from an interrupted run
                             are cleaned out first. Run under `caffeinate` so the Mac
                             will not sleep mid-run.

Usage:
  caffeinate -i python3 analysis/run_stage2.py                 # full crossing
  python3 analysis/run_stage2.py --smoke --out data/stage2_smoke   # quick validation
"""

import argparse, base64, csv, gzip, hashlib, json, os, sys, time
from collections import defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
PROJECT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
import bfg_stage2 as s2

# ---------- locked run spec (also written into the manifest) ----------
SCALARS = [0.25, 0.5, 1.0, 1.5]
ECM = [True, False]
VALLEY_REAPERS = ["top_fitness", "random"]
N_REPS = 20
K_PEAKS = 5
SLOTS_PER_PEAK = 10
VALLEY_CAPACITY = 200
MAX_GENS = 500
DISPLACEMENT = "fitness_based"
FITNESS_RULE = "max_to_nearest"
WORKERS = 8

PER_GEN_FIELDS = ["run_id", "mutation_scalar", "use_ecm", "valley_reaper", "valley_capacity",
                  "slots_per_peak", "generation", "mean_fitness", "max_fitness", "n_full_fit",
                  "peaks_colonized", "n_in_slot", "n_valley"]
SUMMARY_FIELDS = ["run_id", "mutation_scalar", "use_ecm", "valley_reaper", "valley_capacity", "slots_per_peak", "seed",
                  "generations_run", "final_peaks_colonized", "time_to_blanket",
                  "per_peak_convergence", "colonization_source", "occupancy_distribution",
                  "extinction_gen", "pre_extinction_peaks_colonized",
                  "offspring_total", "offspring_ge_gate", "offspring_corrected"]


def load_real_data():
    """Extract the real dict / targets / seeds from the v6 notebook (the canonical data)."""
    nb = json.load(open(os.path.join(HERE, "BFG_Simulation_v6.ipynb")))
    src = "".join(nb["cells"][2]["source"])
    ns = {"base64": base64, "gzip": gzip, "defaultdict": defaultdict}
    try:
        exec(src, ns)  # builds WORD_SET/TG_IDX; final print references an undefined name
    except Exception:
        pass
    return ns["WORD_SET"], ns["TG_IDX"], ns["SEEDS"], ns["TARGETS_RAW"]


def select_peaks(targets, k):
    """Deterministic greedy farthest-point selection on Levenshtein, so the K peaks are
    spread apart. Returns sorted indices. (run1 'far' design.)"""
    chosen = [0]
    while len(chosen) < k:
        best, best_i = -1, None
        for i in range(len(targets)):
            if i in chosen:
                continue
            dmin = min(s2.levenshtein(targets[i], targets[j]) for j in chosen)
            if dmin > best:
                best, best_i = dmin, i
        chosen.append(best_i)
    return sorted(chosen)


def select_peaks_close(targets, k, anchor=0):
    """Anchor on the easiest/most-reachable peak (target 0, the one run1 colonized most) and
    add its k-1 nearest neighbors by Levenshtein. The cluster is reachable AND mutually close,
    so multiple peaks can be colonized and peak-to-peak leaping is testable. (run2 'close' design.)"""
    nbrs = sorted((i for i in range(len(targets)) if i != anchor),
                  key=lambda i: s2.levenshtein(targets[anchor], targets[i]))
    return sorted([anchor] + nbrs[:k - 1])


# ---------- worker ----------
_G = {}


def _init(word_set, tg_idx, peak_strs, seeds, max_gens, ext_gen=None, new_peak_strs=None, colon_fit=None,
          correction_gate=None, gate_threshold=0.90):
    _G["ws"], _G["tg"] = word_set, tg_idx
    _G["peaks"] = s2.make_peaks(peak_strs)
    _G["seeds"] = seeds
    _G["max_gens"] = max_gens
    _G["ext_gen"] = ext_gen
    _G["new_peaks"] = s2.make_peaks(new_peak_strs) if new_peak_strs else None
    _G["colon_fit"] = colon_fit
    _G["correction_gate"] = correction_gate
    _G["gate_threshold"] = gate_threshold


def run_id_of(job):
    sc, ecm, vr, vcap, slots, rep = job
    return f"s{sc}_ecm{int(ecm)}_{vr}_vc{vcap}_sl{slots}_{rep:02d}"


def _run(job):
    scalar, use_ecm, vreaper, vcap, slots, rep = job
    run_id = run_id_of(job)
    seed = int(hashlib.md5(run_id.encode()).hexdigest()[:8], 16)
    ext = _G.get("ext_gen")
    cfg = s2.Stage2Config(
        n_peaks=len(_G["peaks"]), slots_per_peak=slots, valley_capacity=vcap,
        valley_reaper=vreaper, displacement=DISPLACEMENT, fitness_rule=FITNESS_RULE,
        max_generations=_G["max_gens"], mutation_scalar=scalar, use_ecm=use_ecm, seed=seed,
        extinction_gen=ext, colonization_fitness=_G.get("colon_fit"),
        correction_gate=_G.get("correction_gate"), gate_threshold=_G.get("gate_threshold", 0.90),
        stop_on_blanket=(ext is None), no_progress_patience=0)
    out = s2.run_stage2(cfg, _G["peaks"], _G["seeds"], _G["ws"], _G["tg"], run_id=run_id,
                        new_peaks=_G.get("new_peaks"))
    out["seed"] = seed
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
    ap.add_argument("--out", default=os.path.join(PROJECT, "data", "stage2_run1"))
    ap.add_argument("--smoke", action="store_true")
    ap.add_argument("--peaks", default="far", choices=["far", "close"])
    ap.add_argument("--valley-caps", default=str(VALLEY_CAPACITY),
                    help="comma-separated valley_capacity values to sweep")
    ap.add_argument("--scalars", default=",".join(str(s) for s in SCALARS))
    ap.add_argument("--reps", type=int, default=N_REPS)
    ap.add_argument("--vreapers", default=",".join(VALLEY_REAPERS))
    ap.add_argument("--slots", default=str(SLOTS_PER_PEAK),
                    help="comma-separated slots_per_peak values to sweep")
    ap.add_argument("--extinction-gen", type=int, default=0,
                    help="if >0, replace the peaks with a new reachable cluster at this generation")
    ap.add_argument("--max-gens", type=int, default=0,
                    help="override the generation ceiling (0 = default MAX_GENS). Used to hold a "
                         "fixed post-extinction recovery window when sweeping --extinction-gen.")
    ap.add_argument("--peak-indices", default="",
                    help="explicit comma-separated target indices to use as peaks (overrides "
                         "--peaks). Recorded in the manifest. Used for the inter-peak distance sweep.")
    ap.add_argument("--colon-fit", type=float, default=0.0,
                    help="colonization fitness threshold (0 = default exit_fitness 0.99999). Set below "
                         "1.0 to test a relaxed, non-exact colonization criterion.")
    ap.add_argument("--correct-gate", choices=["above", "below"], default=None,
                    help="fitness-gated correction (mechanism test): 'above' corrects only offspring whose "
                         "pre-correction fitness is at or above the gate threshold (near a peak), 'below' "
                         "corrects only those below it. Default (unset) corrects every offspring.")
    ap.add_argument("--gate-threshold", type=float, default=0.90,
                    help="fitness threshold for --correct-gate (default 0.90, the near-target band).")
    ap.add_argument("--drop-target-words", action="store_true",
                    help="ablation: remove the peak targets' words from the correction dictionary and "
                         "rebuild the trigram index, so the codebook does not contain the solution "
                         "vocabulary. Tests whether the correction advantage depends on codebook-"
                         "solution alignment. Seeds/peaks/params otherwise identical to the full-dict run.")
    args = ap.parse_args()
    os.makedirs(args.out, exist_ok=True)
    per_gen_csv = os.path.join(args.out, "stage2_per_generation.csv")
    summary_csv = os.path.join(args.out, "stage2_summary.csv")
    manifest_path = os.path.join(args.out, "manifest.json")

    word_set, tg_idx, seeds, targets = load_real_data()
    kp = 3 if args.smoke else K_PEAKS
    if args.peak_indices.strip():
        peak_idx = sorted(int(x) for x in args.peak_indices.split(","))
        kp = len(peak_idx)
        peak_mode = "explicit"
    else:
        peak_idx = select_peaks_close(targets, kp) if args.peaks == "close" else select_peaks(targets, kp)
        peak_mode = args.peaks
    peak_strs = [targets[i] for i in peak_idx]
    dropped_target_words = 0
    if args.drop_target_words:
        drop = set()
        for ps in peak_strs:
            drop |= set(ps.split())
        drop &= word_set
        dropped_target_words = len(drop)
        word_set, tg_idx = s2.build_index(word_set - drop)
    _G["max_gens"] = (40 if args.smoke else MAX_GENS) if not args.max_gens else args.max_gens
    _G["colon_fit"] = args.colon_fit or None
    _G["correction_gate"] = args.correct_gate
    _G["gate_threshold"] = args.gate_threshold

    # extinction: the new peaks are the NEXT kp targets nearest the anchor (distinct from the
    # old cluster, still reachable), so post-event recovery is observable.
    ext_gen = args.extinction_gen or None
    new_peak_strs, new_idx = None, None
    if ext_gen:
        nbrs = sorted((i for i in range(len(targets)) if i != 0),
                      key=lambda i: s2.levenshtein(targets[0], targets[i]))
        new_idx = sorted(nbrs[kp - 1:2 * kp - 1])
        new_peak_strs = [targets[i] for i in new_idx]

    scalars = [float(x) for x in args.scalars.split(",")]
    vreapers = args.vreapers.split(",")
    vcaps = [int(x) for x in args.valley_caps.split(",")]
    slotsv = [int(x) for x in args.slots.split(",")]
    reps = 1 if args.smoke else args.reps
    # rep-outer ordering: the first pass covers one rep of every condition, so early
    # results sample the whole design and partial results stay balanced.
    jobs = [(sc, ecm, vr, vcap, slots, rep) for rep in range(reps) for sc in scalars
            for ecm in ECM for vr in vreapers for vcap in vcaps for slots in slotsv]

    code_hash = hashlib.md5(open(os.path.join(HERE, "bfg_stage2.py"), "rb").read()).hexdigest()
    manifest = {
        "spec": {"scalars": scalars, "ecm": ECM, "valley_reapers": vreapers,
                 "valley_caps": vcaps, "slots_per_peak": slotsv, "n_reps": reps,
                 "k_peaks": len(peak_idx), "max_generations": _G["max_gens"],
                 "displacement": DISPLACEMENT, "fitness_rule": FITNESS_RULE,
                 "exit_fitness": 0.99999, "children_per_parent": 10, "total_runs": len(jobs),
                 "colonization_fitness": _G.get("colon_fit"),
                 "similarity_threshold": s2.SIMILARITY_THRESHOLD},
        "peak_mode": peak_mode, "peak_indices": peak_idx, "peaks": peak_strs, "seeds": seeds,
        "extinction_gen": ext_gen, "new_peak_indices": new_idx, "new_peaks": new_peak_strs,
        "dictionary_words": len(word_set), "dropped_target_words": dropped_target_words,
        "correction_gate": args.correct_gate, "gate_threshold": args.gate_threshold,
        "bfg_stage2_md5": code_hash, "workers": WORKERS, "smoke": args.smoke,
        "data_source": "BFG_Simulation_v6.ipynb (canonical dict/targets/seeds)",
    }
    json.dump(manifest, open(manifest_path, "w"), indent=2)

    # resume: completed = run_ids with a summary row; clean partial per-gen rows
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
          f"of {len(jobs)} | peaks={peak_idx} | vcaps={vcaps} | out={args.out}", flush=True)

    import multiprocessing as mp
    t0 = time.time()
    done = len(completed)
    with mp.get_context("spawn").Pool(WORKERS, initializer=_init,
                                      initargs=(word_set, tg_idx, peak_strs, seeds, _G["max_gens"],
                                                ext_gen, new_peak_strs, _G.get("colon_fit"),
                                                _G.get("correction_gate"), _G.get("gate_threshold"))) as pool:
        for out in pool.imap_unordered(_run, remaining):
            rid = out["run_id"]
            j = next(j for j in remaining if run_id_of(j) == rid)
            sc, ecm, vr, vcap, slots, rep = j
            for row in out["rows"]:
                row["valley_reaper"] = vr
                row["valley_capacity"] = vcap
                row["slots_per_peak"] = slots
            _append(per_gen_csv, PER_GEN_FIELDS, out["rows"])
            sm = out["summary"]
            _append(summary_csv, SUMMARY_FIELDS, [{
                "run_id": rid, "mutation_scalar": sc, "use_ecm": int(ecm), "valley_reaper": vr,
                "valley_capacity": vcap, "slots_per_peak": slots,
                "seed": out["seed"], "generations_run": sm["generations_run"],
                "final_peaks_colonized": sm["final_peaks_colonized"],
                "time_to_blanket": sm["time_to_blanket"],
                "per_peak_convergence": json.dumps(sm["per_peak_convergence"]),
                "colonization_source": json.dumps(sm["colonization_source"]),
                "occupancy_distribution": json.dumps(sm["occupancy_distribution"]),
                "extinction_gen": sm.get("extinction_gen"),
                "pre_extinction_peaks_colonized": sm.get("pre_extinction_peaks_colonized"),
                "offspring_total": sm.get("offspring_total"),
                "offspring_ge_gate": sm.get("offspring_ge_gate"),
                "offspring_corrected": sm.get("offspring_corrected")}])
            done += 1
            el = time.time() - t0
            rate = (done - len(completed)) / el if el > 0 else 0
            eta = (len(jobs) - done) / rate / 60 if rate > 0 else 0
            print(f"[{time.strftime('%H:%M:%S')}] {done}/{len(jobs)} {rid} "
                  f"gens={sm['generations_run']} colonized={sm['final_peaks_colonized']} "
                  f"ETA~{eta:.0f}m", flush=True)
    print(f"[{time.strftime('%H:%M:%S')}] DONE. {done}/{len(jobs)} runs. "
          f"{time.time()-t0:.0f}s. -> {args.out}", flush=True)


if __name__ == "__main__":
    main()
