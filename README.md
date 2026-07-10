# BFG corrective-replicator simulation

**Project:** Error correction and adaptive search in rugged fitness landscapes
**Authors:** Matthew E. Brashears, Eric Gladstone, Jose Ferrer

A simulation study of error correction in evolving replicator populations. A population of textual
replicators (English sentences) mutates and reproduces while evolving toward target sentences that
define the peaks of a fitness landscape. A correction mechanism repairs variants toward a set of allowed
forms (real dictionary words) without any information about the targets. The study asks how such
correction affects adaptation.

The work has two parts:

- **Single-peak (replication).** Reproduces the earlier result that correction speeds convergence to a
  single peak and buffers a population against mutational degradation. Interactive HTML/JavaScript builds
  are in `simulation/`; the replication notebooks are in `analysis/`.
- **Multi-peak (new).** Replaces global selection with per-peak retention so a population can occupy
  several peaks at once, then asks whether correction increases how many peaks a population reaches and
  settles to completion. It does, and the advantage holds as the peaks are moved apart. The multi-peak
  model is `analysis/bfg_stage2.py` with the harnesses and analysis scripts alongside it.

---

## What to use

| Task | File |
|------|------|
| Interactive single-peak simulation | `simulation/bfg_v6_50-50_ecm80.html` (open in a browser) |
| Multi-peak model | `analysis/bfg_stage2.py` |
| Run multi-peak experiments | `analysis/run_stage2.py` (and the `run_*.sh` drivers) |
| Regenerate the figures | `analysis/make_pub_figures.py`, `analysis/make_schematic.py` |
| Audit the reported numbers | `analysis/audit_recompute.py` |
| Session history and decisions | `docs/BFG_Dev_Log.md` |
| Audit report | `docs/BFG_Audit_Jul9.md` |

## Repository structure

```
analysis/     model (bfg_stage2.py), harnesses (run_*.py, run_*.sh), analysis and figure scripts,
              replication notebooks (BFG_Simulation_v6.ipynb)
simulation/   interactive HTML/JavaScript builds of the single-peak model
data/         per-experiment manifests + per-run summary CSVs (full per-generation data on OSF)
figures/      publication figures (figures/pub/*.png) and original figure panels (SVG)
docs/         development log, audit report, replication notes (Markdown)
```

## Reproducing the results

Every run set carries a `manifest.json` recording the full configuration, the seed list, the peak
identities, and an MD5 hash of the model code, so any run reproduces exactly from the code and its
manifest. A seed-matched check confirmed the model is identical across code versions (see
`docs/BFG_Audit_Jul9.md`). Headline multi-peak estimates pool two independent draws produced under the
current code and are reported with standard errors.

### Data

To keep the repository lean, `data/` here contains the **manifests and per-run summary CSVs** for each
experiment, which reproduce every reported number and figure given the code. The full
**per-generation** output is deposited on the Open Science Framework at https://doi.org/10.17605/OSF.IO/K2PH7.

---

## Model

The simulation follows a five-component loop each generation:

1. **Replicator** — each survivor produces N offspring (exact copies before mutation).
2. **Mutator** — applies stochastic character-level variation to each offspring.
3. **Corrector** — optionally repairs non-words via dictionary lookup (correction condition only).
4. **Evaluator** — scores each offspring against all fitness targets.
5. **Selector** — retains offspring for the next generation (see Selection below).

### Canonical parameters

| Parameter | Value |
|-----------|-------|
| Fitness weighting | 50/50 word / character |
| Correction similarity threshold | 0.80 |
| Mutation rate multipliers | 0.25, 0.5, 1.0, 1.5 |
| Children per parent | 10 |
| Max generations | 500 (extended for the disruption experiment) |
| Exit (exact-match) fitness | 0.99999 |
| Seeds | 16 |
| Targets | 100 sentences |
| Dictionary | 110,879 words (plus target words) |

### Mutation

Five operators, each scaled by the mutation rate multiplier:

| Operator | Base probability |
|---|---|
| Character substitution | 0.02 |
| Character deletion | 0.004 |
| Character insertion | 0.004 |
| Space deletion | 0.02 |
| Space insertion | 0.004 |

Applied per character position in a fixed order. Valid characters: a-z, hyphen, apostrophe.

### Error correction

Applied word by word after mutation. A word found in the dictionary is retained. A word not found is
replaced by a randomly selected candidate meeting a minimum combined trigram and Levenshtein similarity
threshold of 0.80, or left unchanged if no candidate qualifies. Correction has no knowledge of the
fitness targets. Implemented with a custom trigram index and Levenshtein distance.

### Fitness

Each replicator is scored against all targets and keeps its highest score. For a replicator S and target T:

- **Character similarity:** `(len_max - levenshtein(S, T)) / len_max`
- **Word similarity:** `words_shared / words_max` (set-based, unique words only)
- **Combined:** `(word + character) / 2` (equal weighting)

In the multi-peak model, a replicator's fitness is its similarity to its single nearest peak.

### Selection

- **Single-peak (baseline):** global top-N truncation. All offspring are ranked by fitness and the top N
  are retained. Because retention rewards only the fittest across all targets, the population collapses
  onto the easiest peak.
- **Multi-peak (new):** each offspring is assigned to its nearest peak. Each peak has a fixed number of
  genotype slots filled by the fittest replicators nearest it; the remainder wait in a capacity-capped
  valley remnant that is pruned by fitness or at random. A peak is colonized when one of its slot
  occupants reaches an exact match. This lets a population hold several peaks at once.

---

## Deviations from the original Java simulation

| # | Item | Java | This implementation | Reason |
|---|------|------|---------------------|--------|
| 1 | Word scoring | Count-based (multiset) | Set-based | Paper methods text specifies a set of words |
| 2 | Convergence criterion | Fitness equality | String equality | Matches the Java BFG.java source and is more meaningful |
| 3 | Max generations | 1000 (dev config) | 500 | Manuscript specification |
| 4 | Exit fitness threshold | 0.99 | 0.99999 | Matches the Java source, more precise |
| 5 | Levenshtein library | Apache Lucene | rapidfuzz / pure Python | Verified identical results |
| 6 | Word correction | Apache Lucene FuzzyQuery | Custom trigram index | Equivalent algorithm, independently verified |
| 7 | Language | Java | JavaScript and Python | Portability |

## Dictionary

110,879 words: a base English dictionary supplemented with all words appearing in the 100 target
sentences. In the interactive builds it is stored as a gzip-compressed, base64-encoded string with a
trigram index built at load time.

## Citation and license

`[AUTHORS: add a CITATION.cff once the citation form is final, and a LICENSE. MIT for code and CC-BY-4.0
for text and figures are common choices.]`

---

*Export refreshed July 10, 2026.*
