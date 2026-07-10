# github/ — Export folder

Copied materials prepared for GitHub upload. **Not the canonical source.**

## What this is

A staging area for a clean GitHub presentation of the Brashears–Ferrer–Gladstone (BFG)
corrective-replicator simulation work. Files here are copies. Originals remain in the parent project
folder.

## Refresh model

- Treat this folder as **derived**. Do not edit files here as the primary copy.
- When the parent project changes, refresh by re-copying from the canonical source, not by editing the
  export in place.
- Future re-exports may overwrite anything added directly here.

## Refresh log

- **July 10, 2026 — major refresh (multi-peak work).** Added the entire Stage 2 multi-peak model,
  experiments, analysis, and publication figures. The prior export (April/May) held only the single-peak
  replication. See below for what was added and the data policy.

## What was copied (current)

- `README.md` — overview, rewritten to cover the multi-peak work and the export structure.
- `analysis/` — the multi-peak model (`bfg_stage2.py`), network extension (`bfg_stage4.py`), experiment
  harnesses (`run_stage2.py`, `run_stage3.py`, `run_stage4.py`, `run_stage4_decouple.py`, and the
  `run_*.sh` drivers), analysis and figure scripts (`sweep_proximity.py`, `design_distance_ladder.py`,
  `analyze_*.py`, `pool_and_report.py`, `audit_recompute.py`, `make_pub_figures.py`, `make_schematic.py`,
  `pubfig.py`), plus the original replication notebooks and utilities.
- `simulation/` — interactive HTML simulations of the single-peak model.
- `data/` — **manifests and per-run summary CSVs** for every real experiment (single-peak replication,
  multi-peak coverage, distance and capacity sweeps, disruption, and the exploratory Stage 3/4 runs).
- `figures/` — publication figures (`figures/pub/*.png`) plus the original figure panels (SVG) and PPTX.
- `docs/` — `BFG_Dev_Log.md`, `BFG_Audit_Jul9.md`, `Replication_Analysis.md` (Markdown only).
- `original_java/` — **source-only** copy of Jose Ferrer's original Java implementation (51 `.java`
  files, `pom.xml`, config; ~300 KB). See `original_java/ABOUT_THIS_COPY.md`. The build output
  (`target/`), Lucene indices, and stream data (~550 MB) were omitted as regenerable artifacts.

## Data policy (new)

The full per-generation output across all experiments is about 200 MB, most of it regenerable from the
code and the per-run seeds. To keep the repository lean, the export includes **only the manifests and
per-run summary CSVs**, which reproduce every reported number and figure given the code. The full
per-generation data goes to the **OSF deposit** (link to be added to the README and manuscript).

## What was deliberately excluded

- `archive/` — manuscript drafts (`.docx`), PDFs, superseded figures, and the bulky parts of the
  original Java archive (compiled build, Lucene indices, stream data). The Java **source** is included
  under `original_java/` (see above).
- Manuscript and supplementary text (`manuscript/`) — kept out of the code-and-data repo, consistent
  with prior policy. Revisit if a preprint or paper source is wanted in the repo.
- Word-format correspondence and logs (`docs/Claude Log.docx`, `docs/Email Exchange With Matt.docx`).
- `_claude_memory.md`, `CAUTION.md` — private/internal notes.
- Internal document-build tooling (the `*_docx.py` scripts that assemble the Word manuscript and build
  documentation) — not part of the scientific pipeline.
- Per-generation CSVs and `*_smoke*` test folders.

## Outstanding items before upload

- Add a `LICENSE` (MIT for code and CC-BY-4.0 for text and figures are common choices) — author's call.
- Add a `CITATION.cff` once authorship and citation form are finalized.
- Add the OSF link to `README.md` (Data section) and to the manuscript once the deposit exists.
- Confirm the CSVs contain only simulation output and no restricted data (they appear to be simulation
  outputs only).
- Decide whether the exploratory Stage 3/4 runs (a planned follow-up paper) should ship now or be held.
