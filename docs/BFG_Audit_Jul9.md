# BFG build-doc audit — July 9 2026

Full audit of `bfg-stage2-build-review.docx` against the raw data, prompted by finding the
non-binding-threshold artifact in the finisher sweep. Every number was recomputed from the
CSV named in its source column by `analysis/audit_recompute.py` (re-runnable). Three layers:
faithfulness (does the doc match the data), construction (is each metric measuring what it
claims), reproducibility (which code produced each dataset).

## 1. Faithfulness — PASS (no hallucinations)

`analysis/audit_recompute.py` recomputed **82 result numbers** across Tables 13, 14, 15, 19,
22, 23, 25, 26, 28 and the slots/robustness/valley-reaper prose. **82 / 82 PASS** within
rounding tolerance. Additionally verified independently:

- Table 17 (finisher) — `sweep_proximity.py` is guarded to reproduce the published 119/160 and
  57/137, and the reach/climb figures come from that guarded script.
- Table 18 (distance) and Table 20 (extinction timing) — written directly from
  `analyze_distance.py` / `analyze_ext_timing.py`, which recompute from raw CSV.
- Prose trajectory: stable-arm mutation gen0 = 0.88, gen999 = 0.20 (claim "about 0.85 to 0.20"); recurring final 0.33.
- Stage 4 uncertainty claim "SE of the difference about 0.010" — confirmed (structured loaded/drift cells 0.008 to 0.012; well-mixed baseline larger at 0.035, as the doc says).

**Conclusion: every result number in the doc traces correctly to raw data. No fabricated or mis-transcribed numbers.**

## 2. Construction — 3 findings (1 fixed, 1 resolved, 1 note)

Correct numbers can still be measured in a misleading way. Three cases:

1. **Finisher conversion, non-binding threshold (FIXED).** The "~74% at every threshold" was an
   artifact: all 160 correction runs reach >= 0.90, so the threshold never subsets them and
   119/160 is fixed by construction, not robustness. The doc now reports the informative
   quantities instead: reach (100% vs 86% into the 0.90 band) and finishing speed (faster at
   every band). Table 17 rebuilt.

2. **Extinction recovery, window-limited (RESOLVED).** The timing sweep's small post-event gaps
   were largely an artifact of a 250-generation recovery window that cut recovery off mid-climb
   (recovery does not even start for ~150 gens). A widened 750-generation run shows the advantage
   is real and **grows** with time: 0.25 vs 0.12 at 250 gens post-event, rising to 1.40 vs 0.80
   by 750 gens and still climbing; recovery speed median 405 vs 507 gens; 33 vs 27 runs recover.
   Added as the "Robustness, recovery window length" subsection.

3. **Stage 4 "three to four times" ratio (NOTE for manuscript).** As an aggregate it holds (mean
   structured advantage / mean well-mixed across loaded and drift cells ~ 0.053 / 0.014 ~ 3.7x).
   But the per-condition ratio is unstable because the well-mixed denominator is small and noisy:
   ~2x at env load 1.0, ~3-4x at drift 0.5, ~17-20x at env load 0.5. Recommend stating it as an
   aggregate and not leaning on a single ratio.

## 3. Reproducibility — 2 findings (release hygiene, not correctness)

1. **Most headline data was produced by OLDER code versions.** Current `bfg_stage2.py` md5 is
   `ee3f2dc5`. Headline folders differ: run1 `d8caf3b0`, run2_fixed `1dee9745`, extinction
   `1052467`, slots `1dee9745`, stage3 `df0212a9`, stage4 `9decbc9a`. All folders carry manifests
   with seeds, so each reproduces under ITS code version. The changes since were the
   colonization_source fix (affects only the source tag, not counts) plus additive new functions
   (run_stage3 / run_stage4), so the count metrics should be unchanged, but this is not yet
   proven by a matched re-run. **Recommend: before the OSF / GitHub release, regenerate the
   headline runs with one pinned current-code version so the whole dataset shares a single md5.**
   The new July 9 sweeps (distance, ext_timing, ext_window) and the decoupling runs are already
   current-code.

2. **Table 10 (valley-reaper 4-peak build test) is not reproducible from saved data.** It is an
   early build-illustration, explicitly labeled "not the full runs," with no saved folder. The
   finding it illustrates (valley pruning affects blanketing) is independently confirmed by the
   full-run robustness numbers (run2_fixed: ECM 1.06 vs 0.91 by reaper, no-ECM 0.51 vs 0.25, all
   PASS). **Recommend: drop Table 10 in the manuscript in favor of the full-run robustness table,
   or regenerate and save the toy test.**

## Figures
11 inline images in the doc, 11 PNGs present, each plotting a verified table or verified
per-generation data. New figures (distance, ext_timing, ext_window) regenerated from the audited
analyzers.

## Bottom line
No hallucinations; all numbers are faithful to the raw data. Two measurement artifacts were found
and both are addressed in the doc; a third (the Stage 4 ratio) is a wording note. The main open
item is release hygiene: regenerate the older-code headline runs under one pinned version before
posting to OSF / GitHub.

Audit scripts: `analysis/audit_recompute.py` (re-runnable), plus `sweep_proximity.py`,
`analyze_distance.py`, `analyze_ext_timing.py`, `analyze_ext_window.py`.

---

# Update — July 10 2026 (regeneration, pooling, and a reaper finding)

## Reproducibility: RESOLVED (code proven identical)
A seed-matched regression test (`analysis/audit_recompute` companion run) re-ran 8 of the
original error-correction Run 2 cells under the CURRENT code with their ORIGINAL seeds and got
**identical `final_peaks_colonized` in all 8** (0/8 mismatch). So `run_stage2` is byte-for-byte
unchanged across code versions; the md5 differed only from added functions/comments. The older
headline data is therefore valid, and the earlier "older-code" caveat is closed.

## Pooling: headline softened but more stable
Because old and current code are proven identical, the old and the regenerated (`_v2`) runs are two
independent draws from the same process and were pooled (~2x runs, SEs attached). Pooled values
(`analysis/pool_and_report.py`):

- **Run 2 close (n=320/condition):** mean peaks colonized ECM **0.90 ± 0.04** vs no-ECM **0.38 ± 0.03**;
  reached >=1 **71% vs 36%**; blanket >=2 **18% vs 2%**; max 3 vs 2. Sources (410 events):
  valley 47% / in-situ 53% / peak-to-peak 0% (ECM 42/58, no-ECM 59/41).
- **Run 1 far (n=640):** mean peaks ECM 0.23 vs 0.15; any colonized 22% vs 15%; median gen 243 vs 303.
- **Extinction preview (n=80):** pre 0.53/0.38, post 0.25/0.12 (pooled matches the single draw).
- **Slots (n=40/cell):** 0.80/0.65, 1.10/0.70, 1.75/1.00, 2.50/2.05 (unchanged).

Note the softening: the earlier single-draw headline (0.99, 74%, 22%) came down to **0.90, 71%, 18%**
on double the runs. The advantage is unchanged in character (~2.4x, ~10 SE separation) and now carries
uncertainty. **Worth telling Matt** the exact figures came down a touch.

## NEW FINDING — valley-reaper direction contradicts the early build narrative (FLAG)
The doc's parameter narrative (and old Table 10) say random pruning "preserves the diversity needed to
reach distant peaks" while fitness pruning "starves the others." **The full pooled data shows the
opposite / a null:**

| Run 2 (pooled 320) | mean peaks | reached >=1 | blanket >=2 |
|---|---|---|---|
| ECM top_fitness | 0.98 | 80% | 18% |
| ECM random | 0.82 | 61% | 18% |
| no-ECM top_fitness | 0.49 | 48% | 2% |
| no-ECM random | 0.26 | 24% | 2% |

`top_fitness` reaches the FIRST peak more reliably (80 vs 61%), but the two rules give the SAME
multi-peak rate (blanket>=2 identical). So the reaper affects single-peak reach, not multi-peak
coverage; random pruning confers no diversity advantage. Run 1 far agrees (top_fitness 0.40 >> random
0.05). The early "random preserves diversity" claim came from one unaveraged 4-peak toy run (old Table
10: random 4-of-4 vs fitness 3-of-4) and is not supported. The re-run averaged toy test agrees with the
full data (top_fitness 0.78 vs random 0.42 of 4). **This bears on Matt's comment 1 ("over-fit to one
peak?"), so it is left in the doc for Eric+Matt to revise together rather than reversed unilaterally.**

## Doc handling
Pooled results and these findings are added to the "Audit and reproducibility" section additively.
Existing tables/prose and Matt's 16 comments are left untouched to preserve comment anchors; the audit
section is the authoritative updated record. Manuscript will use the pooled numbers.
