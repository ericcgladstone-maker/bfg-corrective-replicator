"""BFG Stage 4 — network topology x error correction.

The manuscript is a networks paper, but Stages 1-3 are well-mixed. The abstract's own
conclusion points here: ECMs as embedded constraints in transmission across ties, and
"topological structures that will interact with ECMs to be more or less generative."

Model: N replicators sit on the nodes of a graph. Each generation, every node looks at a
mutated (and, with ECM, corrected) copy of itself and of each neighbour, and keeps the
fittest variant it can see (selection at reception; a node never loses fitness). So fit
content hill-climbs locally and spreads along ties, transformed by correction in transit.
Topology (how nodes are wired) decides how fast and how far it spreads, and we ask how that
interacts with error correction. Built on the verified core in bfg_stage2.py.
"""

from __future__ import annotations
import random
from dataclasses import dataclass
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bfg_stage2 as s2
from bfg_stage2 import mutate, correct, _score_against, build_index, make_peaks  # verified core


# ---------------- graph builders (pure python, seeded; no networkx dependency) -------------
def ring_lattice(n, k, rng=None):
    adj = [set() for _ in range(n)]
    for i in range(n):
        for d in range(1, k // 2 + 1):
            adj[i].add((i + d) % n); adj[i].add((i - d) % n)
    return [sorted(a) for a in adj]


def watts_strogatz(n, k, p, rng):
    adj = [set() for _ in range(n)]
    for i in range(n):
        for d in range(1, k // 2 + 1):
            adj[i].add((i + d) % n); adj[(i + d) % n].add(i)
    for i in range(n):
        for j in [x for x in adj[i] if x > i]:
            if rng.random() < p:
                adj[i].discard(j); adj[j].discard(i)
                c = rng.randrange(n)
                while c == i or c in adj[i]:
                    c = rng.randrange(n)
                adj[i].add(c); adj[c].add(i)
    return [sorted(a) for a in adj]


def erdos_renyi(n, avg_deg, rng):
    p = avg_deg / (n - 1)
    adj = [set() for _ in range(n)]
    for i in range(n):
        for j in range(i + 1, n):
            if rng.random() < p:
                adj[i].add(j); adj[j].add(i)
    return [sorted(a) for a in adj]


def complete(n, rng=None):
    return [[j for j in range(n) if j != i] for i in range(n)]


def make_graph(topology, n, rng, k=6, rewire_p=0.1):
    if topology == "complete":      # well-mixed control
        return complete(n)
    if topology == "ring_lattice":  # only local ties
        return ring_lattice(n, k)
    if topology == "small_world":   # local + a few long ties
        return watts_strogatz(n, k, rewire_p, rng)
    if topology == "random":        # Erdos-Renyi
        return erdos_renyi(n, k, rng)
    raise ValueError(topology)


@dataclass
class Stage4Config:
    n_nodes: int = 100
    mutation_scalar: float = 1.0
    use_ecm: bool = True
    max_generations: int = 300
    exit_fitness: float = 0.99999
    high_fitness: float = 0.90      # threshold for the "spread" metric
    select_prob: float = 1.0        # decoupling knob A: P(node adopts the FITTEST copy it sees);
                                    # with prob 1-select_prob it adopts a RANDOM transmitted copy
                                    # (fitness-blind drift, so mutation load spreads and only
                                    # correction can clean it). 1.0 = elitist Stage 4 baseline.
    env_scalar: float = 0.0         # decoupling knob B: environmental transmission load applied to
                                    # the ADOPTED copy AFTER selection (so selection-at-reception
                                    # cannot filter it); only correction can clean it. The faithful
                                    # network analogue of Stage 3's env_mut. 0.0 = baseline.
    late_window: int = 100          # final-state averaged over the last this-many generations
    seed: int = 0


def run_stage4(cfg: Stage4Config, peaks, seeds, word_set, tg_idx, graph, run_id="s4"):
    random.seed(cfg.seed)           # mutate/correct use the global RNG
    N = cfg.n_nodes
    fitcache = {}

    def fit(s):
        if s not in fitcache:
            fitcache[s] = max(_score_against(s, ts, tset) for ts, tset in peaks)
        return fitcache[s]

    def transmit(s):
        c = mutate(s, cfg.mutation_scalar)
        if cfg.use_ecm:
            c = correct(c, word_set, tg_idx)
        return c

    nodes = [seeds[i % len(seeds)] for i in range(N)]   # each node starts from a seed
    rows = []
    elitist = cfg.select_prob >= 1.0
    for g in range(cfg.max_generations):
        new = [None] * N
        for i in range(N):
            trans = [transmit(nodes[i])]                # own mutated/corrected copy
            for j in graph[i]:
                trans.append(transmit(nodes[j]))        # mutated/corrected copy from each neighbour
            if elitist:                                 # exact Stage 4 baseline (no extra RNG draw)
                new[i] = max([nodes[i]] + trans, key=fit)
            elif random.random() < cfg.select_prob:     # this node selects the fittest it can see
                new[i] = max([nodes[i]] + trans, key=fit)
            else:                                       # this node drifts: adopt a random transmitted
                new[i] = random.choice(trans)           # copy with NO fitness check (load spreads)
            if cfg.env_scalar:                          # post-selection load only correction can clean
                e = mutate(new[i], cfg.env_scalar)
                new[i] = correct(e, word_set, tg_idx) if cfg.use_ecm else e
        nodes = new
        fits = [fit(s) for s in nodes]
        peaks_col = sum(1 for (ts, tset) in peaks
                        if any(_score_against(s, ts, tset) >= cfg.exit_fitness for s in nodes))
        rows.append({
            "run_id": run_id, "generation": g,
            "mean_fitness": round(sum(fits) / N, 5),
            "max_fitness": round(max(fits), 5),
            "n_full_fit": sum(1 for f in fits if f >= cfg.exit_fitness),
            "frac_high": round(sum(1 for f in fits if f >= cfg.high_fitness) / N, 4),
            "peaks_colonized": peaks_col,
        })
        if all(f >= cfg.exit_fitness for f in fits):     # whole network converged
            break
    late = rows[-cfg.late_window:] if rows else []      # steady state for drift runs (no convergence)
    late_mf = round(sum(r["mean_fitness"] for r in late) / len(late), 5) if late else 0
    late_fh = round(sum(r["frac_high"] for r in late) / len(late), 4) if late else 0
    return {"run_id": run_id, "rows": rows,
            "summary": {"generations_run": len(rows),
                        "final_frac_high": rows[-1]["frac_high"] if rows else 0,
                        "final_peaks_colonized": rows[-1]["peaks_colonized"] if rows else 0,
                        "final_mean_fitness": rows[-1]["mean_fitness"] if rows else 0,
                        "late_mean_fitness": late_mf, "late_frac_high": late_fh}}


if __name__ == "__main__":
    # smoke: small dict, reachable peaks, compare topologies and ECM on/off
    peak_strings = ["the cat sat on the mat", "a dog ran in the park", "birds fly over trees"]
    seed_strings = ["the cat sat on the mat", "some random words to start", "another seed phrase here"]
    vocab = set()
    for s in peak_strings + seed_strings:
        vocab.update(s.split())
    vocab.update(["dog", "cat", "bird", "run", "fly", "park", "tree", "mat", "sun", "blue", "the", "a", "in", "on", "over"])
    ws, tg = build_index(vocab)
    peaks = make_peaks(peak_strings)
    rng = random.Random(0)
    for topo in ("complete", "ring_lattice", "small_world", "random"):
        for ecm in (True, False):
            g = make_graph(topo, 60, random.Random(1), k=6, rewire_p=0.1)
            cfg = Stage4Config(n_nodes=60, max_generations=120, use_ecm=ecm, mutation_scalar=1.0, seed=2)
            out = run_stage4(cfg, peaks, seed_strings, ws, tg, g)
            s = out["summary"]
            print(f"  {topo:13s} ecm={int(ecm)}: gens={s['generations_run']:3d} "
                  f"frac_high={s['final_frac_high']:.2f} peaks_col={s['final_peaks_colonized']} "
                  f"mean_fit={s['final_mean_fitness']:.3f}")
