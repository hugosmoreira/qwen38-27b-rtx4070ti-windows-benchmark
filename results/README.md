# Results

- `raw/` contains append-only run records and raw model responses selected for publication.
- `summaries/` contains derived tables, statistics, and charts.
- `result-schema.example.json` documents the intended record shape before the harness is implemented.

Phases 1 and 2 include proof-of-life records for `UD-IQ2_XXS` and `UD-Q2_K_XL`. They are explicitly classified as `proof_of_life_not_formal_benchmark`; formal repeated measurements begin in Phase 4.

Phase 2 also includes a ten-task objective triage comparison. It supports configuration selection but is explicitly smaller than the planned Phase 8 quality evaluation.

Every summary value must be reproducible from committed raw data and a documented code version. Large diagnostic logs may remain local, but exclusions must be stated.
