# Original Java implementation (source only)

The original BFG simulation by Jose Ferrer — the implementation that the JavaScript and Python versions
in this repository replicate. Provided for historical and reproducibility transparency. The project's
own `README.md` is preserved alongside this note.

**This is a source-only copy.** It contains the Java source (`BFG/src/**`, 51 files), the Maven
`pom.xml`, and the run configuration. The original archive also held a compiled build (`target/`),
prebuilt Apache Lucene dictionary and search indices (`spellNdx/`, `dataNdx/`), and stream data
(`data/*.json`), together about 550 MB. Those are omitted here because they are build output or
regenerable artifacts rather than source.

The JavaScript builds in `../simulation/` and the Python model in `../analysis/bfg_stage2.py` are the
canonical, runnable versions used for the results.
