# Environment Records

This directory records the machine and software environment used for measurements.

- `machine-snapshot-2026-08-15.json` is the Phase 0 static snapshot.
- `model-download-manifest.json` pins the downloaded GGUF repository revision, size, and checksum without storing model weights.
- `phase1-unsloth-runtime-2026-08-15.json` records the managed runtime, first load configuration, memory snapshots, and proof-of-life limitations.
- `phase2-q2-k-xl-preflight-2026-08-15.json` records the next candidate's pinned size and checksum, a clearly labeled memory estimate, and its approval-gated download state.
- `phase2-q2-k-xl-download-manifest.json` records the approved download and checksum validation.
- `phase2-q2-k-xl-runtime-2026-08-15.json` records the actual Q2_K_XL load, corrects the WDDM free-memory projection, and preserves first-generation observations.
- `llama-cpp-b10448-manifest.json` pins the official Windows CUDA 13.3 release assets, published sizes and SHA-256 values, isolated runtime layout, build identity, and CUDA device probe.
- `phase3-native-runtime-2026-08-15.json` records the canonical native launch flags, CUDA layer and buffer evidence, point-in-time memory, OpenAI-compatible smoke result, and setup incidents.
- `phase4-iq2-baseline-2026-08-15.json` records the repeated IQ2 methodology, independently verified aggregates, telemetry cadence and peaks, superseded attempt, and interpretation boundary.
- `phase5-python-runtime-2026-08-15.json` records the supported interpreter, verified official installer checksum, isolated environment policy, zero runtime dependencies, offline tests, and pre-run telemetry probe for the Python harness.
- `phase6-comparison-protocol-2026-08-15.json` freezes the two model manifests, measurement order, controlled settings, calculations, interpretation rules, and exit gate before either Phase 6 result is generated.
- `phase6-comparison-2026-08-15.json` records the fresh IQ2 and Q2 launches, buffer placement, load snapshots, control audit, canonical outputs, post-comparison IQ2 restore, and completed Phase 6 gate.
- `phase7-context-protocol-2026-08-15.json` freezes the selected IQ2 model, 4K/8K/16K order, deterministic fixture sizes and hashes, token budgets, held controls, interpretation thresholds, and failure-preservation rules before canonical context measurement.
- `phase7-context-2026-08-15.json` records the three hash-validated launches, observed CUDA allocations and layer placement, canonical outputs, validation audit, threshold evaluation, transient port-release incident, and restored 4K IQ2 state.
- `phase8-quality-protocol-2026-08-15.json` freezes the 24-task suite hash, paired model order, model checksums, held controls, deterministic graders, paired calculations, interpretation limits, and exit gate before either quant receives a canonical Phase 8 task.
- `phase8-quality-protocol-amendment-2026-08-15.json` discloses the superseded first Q2 attempt, hashes its local server log, and narrows request completion so a received empty answer is preserved as a zero-credit quality result rather than mislabeled as a transport failure.
- `phase8-quality-2026-08-15.json` records both canonical fresh launches, buffer placement, closed local-log hashes, raw-result hashes, control audit, paired result, superseded-attempt boundary, and the healthy fresh IQ2 restore.
- `phase9-mtp-protocol-2026-08-15.json` freezes the isolated IQ2 MTP experiment, two workload hashes, counterbalanced mode order, draft controls, calculation rules, Q3/Q4 deferral, and the excluded capability probe that established llama.cpp's actual MTP timing fields.
- `phase9-mtp-2026-08-15.json` records all four canonical launch/log hashes, buffer evidence, raw-result validation, MTP acceptance, output-equivalence finding, completed decision, and the healthy MTP-off IQ2 restore.
- `phase10-release-protocol-2026-08-15.json` freezes the local `v0.1.0` release gates, public/private boundaries, approval-gated publication sequence, starting audit state, and unresolved owner decisions before repository-surface changes.
- `collect_environment.ps1` in `scripts/` emits a fresh read-only snapshot for later runs.

Environment files must not contain usernames, authentication tokens, full process command lines, or unrelated private paths.
