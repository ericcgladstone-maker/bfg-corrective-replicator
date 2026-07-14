"""BFG Stage 2 — multi-peak simulation.

Built on the VERIFIED core of our replication (mutation, ECM correction, the
50/50 set-based + Levenshtein fitness, max-over-targets), ported verbatim from
BFG_Simulation_v6.ipynb. Stage 2 adds, as configurable pieces, everything the
master build sheet (bfg-stage2-build-review.docx) signs off on:

  - multiple peaks (n_peaks), nearest-peak assignment
  - a per-peak fitness-based reaper (Jose's BucketReaper logic: each peak keeps
    its K fittest occupants; a fitter newcomer bumps the least-fit occupant)
  - a persistent "valley" remnant population
  - lineage tags -> colonization_source (peak-to-peak vs valley) [comment #5]
  - a multi-peak stop condition so runs terminate early [comment #2]
  - coverage outcome measures: peaks_colonized, time_to_blanket,
    per_peak_convergence, occupancy_distribution, colonization_source

Every design choice that is still under discussion with Matt is a field on
Stage2Config with a sensible default, so refinements are config swaps:
  - displacement      : 'fitness_based' (signed off, #3) | 'lowest_slot' (legacy)
  - fitness_rule      : 'max_to_nearest' (recommended) | 'weighted'
  - n_peaks (K)       : start at 5 (#2 runtime)
  - slots_per_peak    : ~10 (TO CONFIRM)
  - valley_capacity   : size of the remnant pool (TO CONFIRM; needed for
                        valley-origin colonization to be observable past gen 0)
  - max_generations   : 500 (confirmed ceiling)
  - stop conditions   : full-blanket / fraction / no-progress patience

The verified single-peak run (run_one) is kept for Stage 1 parity checks.
"""

from __future__ import annotations

import math
import random
from collections import defaultdict
from dataclasses import dataclass, field

# Levenshtein: rapidfuzz on Colab (fast), pure-Python fallback locally.
# The fallback matches the algorithm used in the JS replication.
try:
    from rapidfuzz.distance import Levenshtein as _lev

    def levenshtein(a, b):
        return _lev.distance(a, b)
except ModuleNotFoundError:
    def levenshtein(a, b):
        m, n = len(a), len(b)
        if not m:
            return n
        if not n:
            return m
        prev = list(range(n + 1))
        for i in range(1, m + 1):
            cur = [i] + [0] * n
            ai = a[i - 1]
            for j in range(1, n + 1):
                cur[j] = prev[j - 1] if ai == b[j - 1] else 1 + min(prev[j - 1], prev[j], cur[j - 1])
            prev = cur
        return prev[n]


# =====================================================================
# VERIFIED CORE  (ported verbatim from BFG_Simulation_v6.ipynb, Cell 2)
# Do not modify without re-verifying against the replication.
# =====================================================================

VALID_CHARS = list("abcdefghijklmnopqrstuvwxyz-'")
BASE_RATES = {"sub": 0.02, "del": 0.004, "ins": 0.004, "sd": 0.02, "si": 0.004}
import os as _os
# ECM dictionary match threshold. Default 0.80 (the value used for all prior runs); overridable via
# the BFG_SIM_THRESHOLD environment variable for the correction-threshold sensitivity sweep. Read at
# import so spawn workers inherit it; each process runs one threshold, keeping the correction cache valid.
SIMILARITY_THRESHOLD = float(_os.environ.get("BFG_SIM_THRESHOLD", "0.80"))


def get_trigrams(w):
    n = 2 if len(w) < 3 else 3
    p = " " + w + " "
    return [p[i:i + n] for i in range(len(p) - n + 1)]


def mutate(s, scalar):
    ps = BASE_RATES["sub"] * scalar
    pd = BASE_RATES["del"] * scalar
    pi = BASE_RATES["ins"] * scalar
    psd = BASE_RATES["sd"] * scalar
    psi = BASE_RATES["si"] * scalar
    out = []
    for c in s:
        is_alpha = c.islower() or c in ("-", "'")
        if is_alpha:
            if random.random() >= pd:
                out.append(random.choice(VALID_CHARS) if random.random() < ps else c)
        elif c == " ":
            if random.random() >= psd:
                out.append(c)
        else:
            out.append(c)
        if random.random() < pi:
            out.append(random.choice(VALID_CHARS))
        if random.random() < psi:
            out.append(" ")
    return "".join(out)


_correction_cache = {}


def correct_word(w, word_set, tg_idx):
    if not w or len(w) < 2:
        return w
    if w in word_set:
        return w
    if w in _correction_cache:
        cands = _correction_cache[w]
        return random.choice(cands) if cands else w
    wtgs = set(get_trigrams(w))
    cand_count = defaultdict(int)
    for tg in wtgs:
        if tg in tg_idx:
            for cw in tg_idx[tg]:
                cand_count[cw] += 1
    n = len(w)
    results = []
    for cw in cand_count:
        lmax = max(n, len(cw))
        if (lmax - abs(n - len(cw))) / lmax < SIMILARITY_THRESHOLD:
            continue
        d = levenshtein(w, cw)
        sim = (lmax - d) / lmax
        if sim >= SIMILARITY_THRESHOLD:
            results.append((sim, cw))
    results.sort(reverse=True)
    cands = [cw for _, cw in results[:10]]
    if len(_correction_cache) > 60000:
        _correction_cache.clear()
    _correction_cache[w] = cands if cands else None
    return random.choice(cands) if cands else w


def correct(s, word_set, tg_idx):
    return " ".join(correct_word(w, word_set, tg_idx) if w else w for w in s.split(" "))


def correct_p(s, ecm_q, word_set, tg_idx):
    """Stage 3: each word is corrected with probability ecm_q (the replicator's heritable
    error-correction quality). ecm_q=0 is robust-copying-only, ecm_q=1 is full correction."""
    if ecm_q <= 0:
        return s
    if ecm_q >= 1:
        return correct(s, word_set, tg_idx)
    return " ".join(correct_word(w, word_set, tg_idx) if (w and random.random() < ecm_q) else w
                    for w in s.split(" "))


def _score_against(s, ts, tset):
    """The verified 50/50 word-set + length-normalized Levenshtein score vs one target."""
    lmax = max(len(s), len(ts))
    lsc = (lmax - levenshtein(s, ts)) / lmax if lmax else 1.0
    sw = set(s.split())
    sh = sum(1 for w in sw if w in tset)
    wmax = max(len(sw), len(tset))
    wsc = sh / wmax if wmax else 1.0
    return (wsc + lsc) / 2


def fitness(s, targets):
    """Verified max-over-targets fitness (Stage 1 parity)."""
    return max((_score_against(s, ts, tset) for ts, tset in targets), default=0.0)


def run_one(run_id, scalar, use_ecm, targets, seeds, word_set, tg_idx,
            pop_size=1000, n_children=10, max_gens=500,
            exit_fit=0.99999, exit_count=1000):
    """Verified Stage 1 single-peak run (global top-N reaper). Kept for parity checks."""
    pop = list(seeds)
    cache = {}
    rows = []

    def gf(s):
        if s not in cache:
            cache[s] = fitness(s, targets)
        return cache[s]

    for g in range(max_gens):
        offspring = []
        for parent in pop:
            for _ in range(n_children):
                child = mutate(parent, scalar)
                if use_ecm:
                    child = correct(child, word_set, tg_idx)
                offspring.append(child)
        offspring.sort(key=gf, reverse=True)
        pop = offspring[:pop_size]
        fits = [gf(s) for s in pop]
        rows.append({"run_id": run_id, "generation": g, "mutation_scalar": scalar,
                     "use_ecm": 1 if use_ecm else 0,
                     "mean_fitness": round(sum(fits) / len(fits), 5),
                     "max_fitness": round(fits[0], 5),
                     "n_full_fit": sum(1 for f in fits if f >= exit_fit)})
        if sum(1 for f in fits if f >= exit_fit) >= exit_count:
            break
        if g >= 3 and len(set(pop)) == 1:
            break
    cache.clear()
    return rows


# =====================================================================
# STAGE 2 CONFIG  (each field maps to a master-doc parameter)
# =====================================================================

@dataclass
class Stage2Config:
    # --- Existing (verified) ---
    children_per_parent: int = 10
    max_generations: int = 500          # CONFIRMED ceiling (Jose: published runs were 500)
    exit_fitness: float = 0.99999
    mutation_scalar: float = 1.0
    use_ecm: bool = True
    seed: int = 0
    # fitness-gated correction (mechanism test). None = correct every offspring (default).
    # 'above' = correct only offspring whose PRE-correction fitness >= gate_threshold (near a peak).
    # 'below' = correct only offspring whose PRE-correction fitness < gate_threshold (far from peaks).
    correction_gate: str | None = None
    gate_threshold: float = 0.90

    # --- Stage 2: peaks & selection ---
    n_peaks: int = 5                    # K (start small per comment #2)
    slots_per_peak: int = 10            # niche capacity (TO CONFIRM)
    peak_assignment: str = "nearest"    # 'nearest' (argmax peak)
    displacement: str = "fitness_based"  # 'fitness_based' (#3, signed off) | 'lowest_slot' (legacy)
    fitness_rule: str = "max_to_nearest"  # 'max_to_nearest' | 'weighted'
    weighted_softmax_temp: float = 0.1  # only used when fitness_rule == 'weighted'

    # --- Stage 2: valley remnant (needed so valley-origin colonization is observable) ---
    valley_capacity: int = 200          # TO CONFIRM. 0 => pure bucket (no persistent valley)
    valley_reaper: str = "top_fitness"  # 'top_fitness' | 'random'

    # --- Stage 2: colonization & stop condition (#2) ---
    colonization_fitness: float | None = None  # None => use exit_fitness
    blanket_fraction: float = 1.0       # fraction of peaks colonized that counts as "blanketed"
    stop_on_blanket: bool = True        # stop once blanket_fraction of peaks are colonized
    no_progress_patience: int = 50      # stop after this many gens with no new colonization (0=off)

    # --- Stage 3 preview: extinction event ---
    extinction_gen: int = None          # if set, at this generation the peaks are replaced by
                                        # new_peaks (passed to run_stage2) and colonization
                                        # tracking resets, so post-event re-colonization is measured

    def colon_fit(self):
        return self.exit_fitness if self.colonization_fitness is None else self.colonization_fitness


# =====================================================================
# helpers
# =====================================================================

def build_index(words):
    """Build (word_set, trigram_index) for the corrector — same structure as the replication."""
    word_set = set(words)
    tg_idx = defaultdict(list)
    for w in word_set:
        for tg in get_trigrams(w):
            tg_idx[tg].append(w)
    return word_set, dict(tg_idx)


def make_peaks(target_strings):
    """A peak is (target_string, target_word_set), like the verified `targets`."""
    return [(t, set(t.split())) for t in target_strings]


# =====================================================================
# STAGE 2 RUN
# =====================================================================

def run_stage2(cfg: Stage2Config, peaks, seeds, word_set, tg_idx, run_id="s2", new_peaks=None):
    """One Stage 2 run. `peaks` = output of make_peaks (the K peaks).

    Returns dict with per-generation rows and a run-level summary including the
    new coverage measures.
    """
    random.seed(cfg.seed)
    K = len(peaks)
    colon_fit = cfg.colon_fit()

    comp_cache = {}

    def components(s):
        """Per-peak scores for string s (cached)."""
        if s not in comp_cache:
            comp_cache[s] = [_score_against(s, ts, tset) for ts, tset in peaks]
        return comp_cache[s]

    def assign(s):
        """Return (nearest_peak_idx, fitness_to_that_peak) under the configured fitness rule."""
        comps = components(s)
        if cfg.fitness_rule == "weighted":
            # soft aggregate: still report the argmax peak, but fitness is a
            # temperature-weighted blend across peaks (hook for the alternative rule).
            mx = max(comps)
            ws = [math.exp((c - mx) / cfg.weighted_softmax_temp) for c in comps]
            z = sum(ws)
            blended = sum(w * c for w, c in zip(ws, comps)) / z
            return max(range(K), key=lambda i: comps[i]), blended
        # default: max-to-nearest
        best_i = max(range(K), key=lambda i: comps[i])
        return best_i, comps[best_i]

    # population members: dict(s=str, src=location-of-parent: int peak idx or 'valley')
    population = [{"s": s, "src": "valley"} for s in seeds]

    rows = []
    colonized = {}            # peak_idx -> generation first colonized to full fitness
    colonization_source = {}  # peak_idx -> 'valley' | 'in_situ' | 'peak:<j>'
    last_new_colonization = 0
    pre_ext_colonized = None   # peaks colonized just before an extinction event (if any)
    n_offspring = n_ge_gate = n_corrected = 0  # correction-exposure diagnostics

    for g in range(cfg.max_generations):
        # Stage 3: extinction event. Replace the peaks with a new set, displace every
        # survivor into the valley (their old peak no longer exists), and reset colonization
        # tracking so that what we record afterward is RE-colonization of the new peaks.
        if cfg.extinction_gen is not None and g == cfg.extinction_gen and new_peaks is not None:
            pre_ext_colonized = len(colonized)
            peaks = new_peaks
            K = len(peaks)
            comp_cache.clear()
            colonized.clear()
            colonization_source.clear()
            last_new_colonization = g
            for p in population:
                p["loc"] = "valley"

        # 1. reproduce: each child carries its parent's CURRENT location as src
        offspring = []
        for p in population:
            for _ in range(cfg.children_per_parent):
                cs = mutate(p["s"], cfg.mutation_scalar)
                n_offspring += 1
                if cfg.use_ecm:
                    if cfg.correction_gate is None:
                        cs = correct(cs, word_set, tg_idx); n_corrected += 1
                    else:
                        # decide from the mutated (pre-correction) fitness to its nearest peak
                        pre_fit = assign(cs)[1]
                        if pre_fit >= cfg.gate_threshold:
                            n_ge_gate += 1
                        gate = (pre_fit >= cfg.gate_threshold) if cfg.correction_gate == "above" \
                            else (pre_fit < cfg.gate_threshold)
                        if gate:
                            cs = correct(cs, word_set, tg_idx); n_corrected += 1
                # child's src = the parent's CURRENT location (peak idx or 'valley').
                # seeds have no 'loc' yet, so they default to 'valley'.
                offspring.append({"s": cs, "src": p.get("loc", "valley")})

        # 2. assign each offspring to its nearest peak + record fitness
        for o in offspring:
            o["peak"], o["fit"] = assign(o["s"])

        # 3. per-peak reaper: keep the slots_per_peak fittest at each peak (fitness-based
        #    eviction = a fitter newcomer bumps the least-fit occupant). #3 signed off.
        by_peak = defaultdict(list)
        for o in offspring:
            by_peak[o["peak"]].append(o)
        in_slot, leftover = [], []
        for pk, members in by_peak.items():
            members.sort(key=lambda o: o["fit"], reverse=True)
            if cfg.displacement == "lowest_slot":
                # legacy position-based variant (kept as a switch); same top-K here
                keep = members[:cfg.slots_per_peak]
            else:
                keep = members[:cfg.slots_per_peak]  # fitness_based
            for o in keep:
                o["loc"] = pk
            in_slot.extend(keep)
            leftover.extend(members[cfg.slots_per_peak:])

        # 4. valley remnant: keep a capped pool of the non-slot offspring
        if cfg.valley_capacity > 0 and leftover:
            if cfg.valley_reaper == "random":
                random.shuffle(leftover)
                valley = leftover[:cfg.valley_capacity]
            else:
                leftover.sort(key=lambda o: o["fit"], reverse=True)
                valley = leftover[:cfg.valley_capacity]
            for o in valley:
                o["loc"] = "valley"
        else:
            valley = []

        survivors = in_slot + valley

        # 5. colonization detection (first full-fit occupant of each peak)
        new_this_gen = False
        for o in in_slot:
            pk = o["peak"]
            if pk not in colonized and o["fit"] >= colon_fit:
                colonized[pk] = g
                src = o["src"]
                if src == "valley":
                    colonization_source[pk] = "valley"
                elif src == pk:
                    colonization_source[pk] = "in_situ"
                else:
                    colonization_source[pk] = f"peak:{src}"
                new_this_gen = True
        if new_this_gen:
            last_new_colonization = g

        # 6. per-generation metrics
        fits = [o["fit"] for o in survivors]
        peaks_colonized = len(colonized)
        rows.append({
            "run_id": run_id, "generation": g,
            "mutation_scalar": cfg.mutation_scalar, "use_ecm": 1 if cfg.use_ecm else 0,
            "mean_fitness": round(sum(fits) / len(fits), 5) if fits else 0.0,
            "max_fitness": round(max(fits), 5) if fits else 0.0,
            "n_full_fit": sum(1 for f in fits if f >= cfg.exit_fitness),
            "peaks_colonized": peaks_colonized,
            "n_in_slot": len(in_slot), "n_valley": len(valley),
        })

        # 7. stop conditions (#2): blanket reached, or no progress, or ceiling
        if peaks_colonized >= math.ceil(cfg.blanket_fraction * K):
            if cfg.stop_on_blanket:
                break
        if cfg.no_progress_patience and (g - last_new_colonization) >= cfg.no_progress_patience \
                and peaks_colonized > 0:
            break

        population = survivors
        if not population:  # extinction safety
            break

    # run-level summary
    occupancy = defaultdict(int)
    for o in in_slot:
        occupancy[o["peak"]] += 1
    time_to_blanket = next((r["generation"] for r in rows
                            if r["peaks_colonized"] >= math.ceil(cfg.blanket_fraction * K)), None)
    return {
        "run_id": run_id,
        "rows": rows,
        "summary": {
            "peaks": K,
            "final_peaks_colonized": len(colonized),
            "time_to_blanket": time_to_blanket,
            "per_peak_convergence": dict(colonized),
            "colonization_source": dict(colonization_source),
            "occupancy_distribution": dict(occupancy),
            "generations_run": rows[-1]["generation"] + 1 if rows else 0,
            "extinction_gen": cfg.extinction_gen,
            "pre_extinction_peaks_colonized": pre_ext_colonized,
            "offspring_total": n_offspring,
            "offspring_ge_gate": n_ge_gate,
            "offspring_corrected": n_corrected,
        },
    }


# =====================================================================
# STAGE 3 — heritable mutation rate and error-correction quality, with
# (optionally recurring) extinctions. The question: does selection raise
# error-correction quality over time, and more so across extinctions?
# =====================================================================

@dataclass
class Stage3Config:
    children_per_parent: int = 10
    max_generations: int = 1000
    exit_fitness: float = 0.99999
    slots_per_peak: int = 10
    valley_capacity: int = 200
    valley_reaper: str = "top_fitness"
    # heritable genes (each replicator carries its own mutation rate and ECM quality)
    mut_init: tuple = (0.25, 1.5)   # initial spread of mutation rate
    ecm_init: tuple = (0.0, 1.0)    # initial spread of ECM quality (prob a word is corrected)
    mut_drift: float = 0.06         # heritable drift, multiplicative (lognormal sigma)
    ecm_drift: float = 0.04         # heritable drift, additive (gaussian sd), clamped [0,1]
    mut_min: float = 0.02
    mut_max: float = 3.0
    env_mut: float = 0.0            # unavoidable environmental mutation (NOT heritably suppressible);
                                    # only correction can clean it up -> decouples ECM from mutation rate
    extinction_period: int = 0      # 0 = no extinction; else wipe+replace peaks every N gens
    seed: int = 0


def run_stage3(cfg: Stage3Config, peak_sets, seeds, word_set, tg_idx, run_id="s3"):
    """peak_sets is a list of peak clusters (each from make_peaks). The run starts on
    peak_sets[0]; at each extinction it advances to the next (wrapping). Returns per-generation
    rows tracking population-mean mutation rate and ECM quality (the evolving strategy)."""
    import statistics as _st
    rng = random.Random(cfg.seed)
    epoch = 0
    peaks = peak_sets[0]
    K = len(peaks)
    comp_cache = {}

    def best_fit(s):
        if s not in comp_cache:
            comp_cache[s] = max(_score_against(s, ts, tset) for ts, tset in peaks)
        return comp_cache[s]

    def assign(s):
        if s not in comp_cache:
            comp_cache[s] = max(_score_against(s, ts, tset) for ts, tset in peaks)
        comps = [_score_against(s, ts, tset) for ts, tset in peaks]
        bi = max(range(K), key=lambda i: comps[i])
        return bi, comps[bi]

    # initial population: seeds, each given a random strategy (mut, ecm)
    population = [{"s": s, "mut": rng.uniform(*cfg.mut_init), "ecm": rng.uniform(*cfg.ecm_init),
                   "loc": "valley"} for s in seeds]

    rows = []
    extinctions = []
    for g in range(cfg.max_generations):
        # recurring extinction: swap to the next peak set, displace everyone
        if cfg.extinction_period and g > 0 and g % cfg.extinction_period == 0:
            epoch += 1
            peaks = peak_sets[epoch % len(peak_sets)]
            K = len(peaks)
            comp_cache.clear()
            extinctions.append(g)
            for p in population:
                p["loc"] = "valley"

        # reproduce: traits inherited with drift; mutation uses the child's own rate;
        # correction is applied per word with the child's own ECM quality.
        offspring = []
        for p in population:
            for _ in range(cfg.children_per_parent):
                cmut = min(cfg.mut_max, max(cfg.mut_min, p["mut"] * math.exp(rng.gauss(0, cfg.mut_drift))))
                cecm = min(1.0, max(0.0, p["ecm"] + rng.gauss(0, cfg.ecm_drift)))
                cs = mutate(p["s"], cmut)                       # own copying (heritably suppressible)
                if cfg.env_mut:
                    cs = mutate(cs, cfg.env_mut)                # environmental load (not suppressible)
                cs = correct_p(cs, cecm, word_set, tg_idx)      # correction cleans up both
                offspring.append({"s": cs, "mut": cmut, "ecm": cecm})

        for o in offspring:
            o["peak"], o["fit"] = assign(o["s"])

        # per-peak reaper (keep the slots_per_peak fittest per peak) + valley remnant
        by_peak = defaultdict(list)
        for o in offspring:
            by_peak[o["peak"]].append(o)
        in_slot, leftover = [], []
        for pk, members in by_peak.items():
            members.sort(key=lambda o: o["fit"], reverse=True)
            keep = members[:cfg.slots_per_peak]
            for o in keep:
                o["loc"] = pk
            in_slot.extend(keep)
            leftover.extend(members[cfg.slots_per_peak:])
        if cfg.valley_capacity > 0 and leftover:
            leftover.sort(key=lambda o: o["fit"], reverse=True)
            valley = leftover[:cfg.valley_capacity]
            for o in valley:
                o["loc"] = "valley"
        else:
            valley = []
        survivors = in_slot + valley
        if not survivors:
            break

        peaks_col = sum(1 for pk, members in by_peak.items()
                        if any(o["fit"] >= cfg.exit_fitness for o in members[:cfg.slots_per_peak]))
        rows.append({
            "run_id": run_id, "generation": g, "epoch": epoch,
            "mean_fitness": round(_st.mean(o["fit"] for o in survivors), 5),
            "max_fitness": round(max(o["fit"] for o in survivors), 5),
            "peaks_colonized": peaks_col,
            "mean_mut": round(_st.mean(o["mut"] for o in survivors), 4),
            "mean_ecm": round(_st.mean(o["ecm"] for o in survivors), 4),
            "n": len(survivors),
        })
        population = survivors

    return {"run_id": run_id, "rows": rows,
            "summary": {"extinctions": extinctions, "generations_run": len(rows),
                        "final_mean_mut": rows[-1]["mean_mut"] if rows else None,
                        "final_mean_ecm": rows[-1]["mean_ecm"] if rows else None}}


# =====================================================================
# smoke test (small synthetic data) — validates mechanics fast
# =====================================================================

if __name__ == "__main__":
    # tiny, fast setup: short peaks, a small dictionary, a couple of seeds
    peak_strings = ["the quick brown fox", "a lazy yellow dog", "bright red kite"]
    seed_strings = ["the quick brown fox", "some random starting words here"]
    vocab = set()
    for s in peak_strings + seed_strings:
        vocab.update(s.split())
    vocab.update(["cat", "hat", "sun", "moon", "tree", "blue", "green", "fast", "slow"])
    word_set, tg_idx = build_index(vocab)
    peaks = make_peaks(peak_strings)

    cfg = Stage2Config(n_peaks=len(peaks), slots_per_peak=5, valley_capacity=40,
                       max_generations=120, mutation_scalar=1.0, use_ecm=True, seed=1)
    out = run_stage2(cfg, peaks, seed_strings, word_set, tg_idx, run_id="smoke")
    s = out["summary"]
    print("generations run     :", s["generations_run"])
    print("peaks               :", s["peaks"])
    print("peaks colonized     :", s["final_peaks_colonized"])
    print("time_to_blanket     :", s["time_to_blanket"])
    print("per_peak_convergence:", s["per_peak_convergence"])
    print("colonization_source :", s["colonization_source"])
    print("occupancy_dist      :", s["occupancy_distribution"])
    print("last row            :", out["rows"][-1])
