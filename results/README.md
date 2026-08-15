# Results

- `raw/` contains append-only run records and raw model responses selected for publication.
- `summaries/` contains derived tables, statistics, and charts.
- `result-schema.example.json` documents the intended record shape before the harness is implemented.

Phase 1 includes one proof-of-life record. It is explicitly classified as `proof_of_life_not_formal_benchmark`; formal repeated measurements begin in Phase 4.

Every summary value must be reproducible from committed raw data and a documented code version. Large diagnostic logs may remain local, but exclusions must be stated.
