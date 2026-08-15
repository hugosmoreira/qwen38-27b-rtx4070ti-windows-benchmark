# Results

- `raw/` contains append-only run records and raw model responses selected for publication.
- `summaries/` contains derived tables, statistics, and charts.
- `result-schema.example.json` documents the intended record shape before the harness is implemented.

Phases 1 through 3 include proof-of-life records for `UD-IQ2_XXS`, `UD-Q2_K_XL`, and the pinned native llama.cpp API. They are explicitly classified as proof-of-life rather than formal benchmarks; repeated measurements begin in Phase 4.

Phase 2 also includes a ten-task objective triage comparison. It supports configuration selection but is explicitly smaller than the planned Phase 8 quality evaluation.

Phase 3 retains both the failed 1/3 parser-configuration run and the corrected 3/3 run. Failed evidence is not deleted when it explains a configuration decision.

Every summary value must be reproducible from committed raw data and a documented code version. Large diagnostic logs may remain local, but exclusions must be stated.
