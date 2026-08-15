# Environment Records

This directory records the machine and software environment used for measurements.

- `machine-snapshot-2026-08-15.json` is the Phase 0 static snapshot.
- `model-download-manifest.json` pins the downloaded GGUF repository revision, size, and checksum without storing model weights.
- `phase1-unsloth-runtime-2026-08-15.json` records the managed runtime, first load configuration, memory snapshots, and proof-of-life limitations.
- `phase2-q2-k-xl-preflight-2026-08-15.json` records the next candidate's pinned size and checksum, a clearly labeled memory estimate, and its approval-gated download state.
- `phase2-q2-k-xl-download-manifest.json` records the approved download and checksum validation.
- `phase2-q2-k-xl-runtime-2026-08-15.json` records the actual Q2_K_XL load, corrects the WDDM free-memory projection, and preserves first-generation observations.
- `collect_environment.ps1` in `scripts/` emits a fresh read-only snapshot for later runs.

Environment files must not contain usernames, authentication tokens, full process command lines, or unrelated private paths.
