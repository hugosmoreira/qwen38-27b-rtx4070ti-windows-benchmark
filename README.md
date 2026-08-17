# Qwen3.8-27B on an RTX 4070 Ti 12GB

> A reproducible Windows study of low-bit quantization, GPU residency, context sensitivity, speed, memory, and objective response quality.

## Status

**Phase 9 completed locally on 2026-08-15.** In-model `draft-mtp` increased IQ2 generation throughput by 47.284% on prose and 92.651% on Python code, with 55.187% and 90.110% draft-token acceptance. It also added 554–568 MiB sampled peak VRAM. Code output matched exactly, but prose diverged at generated token 16 under greedy decoding, so MTP remains off by default. Q3 and Q4 were deferred from the `v0.1.0` evidence bundle.

**Phase 10 is public on GitHub as of 2026-08-16.** The Apache-2.0 `v0.1.0` candidate, citation metadata, canonical evidence, and reproducibility tooling are available at [hugosmoreira/qwen38-27b-rtx4070ti-windows-benchmark](https://github.com/hugosmoreira/qwen38-27b-rtx4070ti-windows-benchmark). The Windows CI matrix passes on Python 3.11 and 3.14 after the hosted-runner path normalization in commit [`8ae9061`](https://github.com/hugosmoreira/qwen38-27b-rtx4070ti-windows-benchmark/commit/8ae9061e54c45e32e906be636bbf2a26275d9a83). The candidate is not yet tagged or published as a GitHub Release.

**Phase 11 completed on 2026-08-16.** The evidence-linked report is public as [Hugging Face Community Discussion #65](https://huggingface.co/unsloth/Qwen3.8-27B-GGUF/discussions/65). It was published by `Hugosmr` with all 25 GitHub evidence links and the study limitations intact; no model weights or runtime artifacts were uploaded.

**Phase 12 communication preparation started on 2026-08-16.** The local-first package includes an evidence-checked LinkedIn draft, an eight-post X thread, and a reusable benchmark card. No social post has been published, and the separate `v0.1.0` GitHub tag/release remains approval-gated.

**Phase 13 started on 2026-08-16.** The owner separately authorized an `IQ4_XS` hybrid-offload study. The official artifact is pinned at 15,705,861,088 bytes (14.63 GiB), revision `f1bfb127…`, and SHA-256 `9fd40d70…`; storage preflight passed with more than 1.5 TiB free on the model drive. No Phase 13 throughput or context result is claimed until the download validates and the frozen offload-frontier protocol runs.

The practical recommendation is now stronger: keep IQ2 as the default because Phase 6 measured it 14.759% faster with 1,583 MiB less peak VRAM, while Phase 8 found only a one-task Q2 edge. The largest sensible tested IQ2 context remains 16K under the study's precommitted thresholds; that is not a claim about arbitrary full-window prompts, larger contexts, or long-context retrieval quality.

The Phase 9 speed claims come only from four committed five-repetition records. The earlier 64-token capability probe remains excluded and was used only to validate MTP operation and identify `draft_n` and `draft_n_accepted`.

## Phase 1 proof of life

| Item | Observed value |
|---|---:|
| Model | `Qwen3.8-27B-UD-IQ2_XXS.gguf` |
| Model SHA-256 | `8d1b37297d6cf98303cd396896f35e01089ddcc904053a9c6997f7a1c35b8524` |
| Context | 4,096 tokens |
| Model layers | 65, launched with llama.cpp `-ngl -1` |
| KV cache | Q8 for K and V |
| Parallel slots | 1 |
| Flash attention | Enabled |
| Speculative decoding / MTP | Disabled |
| Thinking / tools / vision | Disabled for the smoke requests |
| Loaded VRAM snapshot | 8,958 MiB used; 3,037 MiB free |
| Server-side load time | 7,125.47 ms |
| Smoke checks | 3/3 passed |

The first short generation reported 44.3 generation tokens/s and 364.9 prompt tokens/s in Unsloth's engine log. These are diagnostic observations, not headline benchmark claims. See the [runtime record](environment/phase1-unsloth-runtime-2026-08-15.json) and [canonical raw smoke result](results/raw/phase1-smoke-20260815T225920Z.json).

## Research question

> Can Qwen3.8-27B be used practically on a 12 GB RTX 4070 Ti under Windows, and how do quantization, GPU residency, context length, speed, memory, and response quality trade off on this machine?

This is deliberately different from an RTX 4090 showcase. The 12 GB VRAM limit creates an engineering tradeoff between:

- quantization level and potential quality;
- GPU residency and CPU/RAM offload;
- context length and KV-cache memory;
- generation speed and response quality.

## Starting hardware

| Component | Verified value |
|---|---|
| GPU | NVIDIA GeForce RTX 4070 Ti |
| VRAM | 12,282 MiB total; approximately 11,612 MiB free during inspection |
| CPU | Intel Core i7-14700K; 28 logical processors |
| RAM | 63.77 GB usable |
| OS | Windows, version 25H2, build 26200.9168 |
| NVIDIA driver | 610.88 |
| Driver CUDA runtime | 13.3 |
| Model/result drive | `E:` with approximately 1.53 TB free at inspection |

## Model configurations

| Configuration | File size | Intended role |
|---|---:|---|
| `UD-IQ2_XXS` | 8.39 GiB | Tested practical default and MTP experiment target |
| `UD-Q2_K_XL` | 9.94 GiB | Tested controlled comparison candidate with tighter VRAM headroom |
| `UD-Q3_K_XL` | 12.52 GiB | Deferred partial-offload candidate |
| `UD-Q4_K_XL` | 16.69 GiB | Deferred heavier-offload candidate |
| `IQ4_XS` | 14.63 GiB | Phase 13 pinned hybrid-offload candidate |

IQ2 and Q2 have been downloaded and tested. Phase 13 authorizes only the pinned `IQ4_XS` artifact; the similarly named `Q4_K_M`, `UD-Q4_K_XL`, and MLX formats are not interchangeable experimental inputs.

## Repository map

```text
.
├── README.md
├── PROJECT.md
├── REPRODUCING.md
├── RELEASE_NOTES.md
├── CONTRIBUTING.md
├── CODE_OF_CONDUCT.md
├── CITATION.cff
├── LICENSE
├── assets/
├── configs/
├── environment/
├── prompts/
├── reports/
├── release/
├── results/
│   ├── raw/
│   └── summaries/
├── scripts/
├── schemas/
├── src/
├── tests/
└── pyproject.toml
```

## Citation, license, and community

The repository's citation metadata identifies Hugo Moreira as the author of the `v0.1.0` software and evidence bundle. See [CITATION.cff](CITATION.cff) for machine-readable metadata that GitHub and archival tools can render.

The benchmark software and repository material are licensed under [Apache-2.0](LICENSE), except for the adapted [Code of Conduct](CODE_OF_CONDUCT.md), which identifies its separate CC BY-SA 4.0 terms. Contributions are governed by [CONTRIBUTING.md](CONTRIBUTING.md), and sensitive vulnerabilities should follow [SECURITY.md](SECURITY.md).

- [PROJECT.md](PROJECT.md) — phase gates, scope, methodology, and publication plan.
- [REPRODUCING.md](REPRODUCING.md) — clean-clone evidence verification and hardware reproduction.
- [RELEASE_NOTES.md](RELEASE_NOTES.md) — `v0.1.0` findings, boundaries, and publication state.
- [CONTRIBUTING.md](CONTRIBUTING.md) — evidence, test, and pull-request requirements.
- `assets/` — reviewed publication graphics; these summarize rather than replace evidence.
- `configs/` — versioned experiment inputs that bind runtime, model, prompt, and controls.
- `environment/` — machine snapshots and environment collection notes.
- `prompts/` — version-controlled benchmark prompts.
- `results/raw/` — append-only machine-readable run data.
- `results/summaries/` — derived tables and charts.
- `reports/` — GitHub, Hugging Face, and social-report drafts.
- `release/` — canonical, superseded, and diagnostic evidence classification.
- `scripts/` — repeatable PowerShell entry points.
- `schemas/` — formal performance and quality result contracts.
- `src/` — benchmark client and telemetry code.
- `tests/` — tests for our code, schemas, and calculations.

## Verify the committed evidence

No GPU or model weights are needed to run the software tests and ordinary release audit:

```powershell
.\scripts\setup_python.ps1
.\scripts\run_python_tests.ps1
$env:PYTHONPATH = (Resolve-Path .\src).Path
.\.venv\Scripts\python.exe -m qwen_bench release-audit --repository-root .
```

The audit parses all tracked JSON with duplicate-key rejection, validates canonical Phase 5–9 records, checks every repository-relative Markdown link, classifies every raw record, and rejects tracked private or oversized artifacts. See [REPRODUCING.md](REPRODUCING.md) for exact result-validation and hardware workflows.

## Reproduce the Phase 1 smoke check

With Unsloth Desktop running and the pinned model already loaded using the Phase 1 settings:

```powershell
.\scripts\run_phase1_smoke.ps1
```

The script authenticates only through Unsloth Desktop's local secret, verifies the active model and configuration, disables thinking and tools in every request, and creates a unique non-overwriting JSON record under `results/raw/`. It never writes a password, token, or local username to the result.

## Reproducibility commitments

- Pin model filename and repository revision.
- Pin the llama.cpp or Unsloth Desktop version.
- Record context, KV-cache type, GPU offload, thinking mode, sampling, MTP, and vision state.
- Run warm-ups and repeated measured trials.
- Preserve failed and out-of-memory runs.
- Use `null`, never invented zeroes, for unavailable metrics.
- Do not commit GGUF model weights, caches, secrets, or unreviewed private prompt data.

## Phase 2 preliminary proof of life

The approved `UD-Q2_K_XL` candidate was downloaded, checksum-validated, and loaded with the same controls as Phase 1:

| Item | Observed value |
|---|---|
| File | `Qwen3.8-27B-UD-Q2_K_XL.gguf` |
| Pinned repository commit | `1cff334a4a228324d4ee1f76d55d372588f0d556` |
| Size | 10,676,423,744 bytes / 9.94 GiB |
| SHA-256 | `46151b52a5cad673d90a00222103254864326c251130b8fc4381d6f34386b3c8` |
| Local location | `models/Qwen3.8-27B-GGUF/Qwen3.8-27B-UD-Q2_K_XL.gguf` |
| Model layers | 65, launched with llama.cpp `-ngl -1`; no CPU fallback |
| Context / KV cache / slots | 4,096 / Q8 K+V / 1 |
| Loaded VRAM snapshot | 10,542 MiB used / 1,453 MiB free |
| Server-side load time | 8,781.03 ms |
| First short engine observation | 38.9 generation tok/s; 418.6 prompt tok/s |
| Canonical smoke checks | 3/3 passed |

The original used-memory projection was within 5.18 MiB, but its free-memory calculation incorrectly used total minus used VRAM. WDDM left about 287 MiB reserved or otherwise unavailable, so the correct projection was 1,447.82 MiB free—close to the 1,453 MiB observation. The [runtime record](environment/phase2-q2-k-xl-runtime-2026-08-15.json) preserves the correction.

The [canonical Q2_K_XL smoke record](results/raw/quant-smoke-ud-q2-k-xl-20260815T232000Z.json) passed 3/3 checks from committed harness revision `d21abea`. The [Phase 2 smoke checkpoint](results/summaries/phase2-smoke-checkpoint.md) compares both quants without presenting the tiny runs as a formal benchmark.

Phase 2 quant triage is complete. On ten identical objective pass@1 tasks, `UD-IQ2_XXS` passed 3/10 and `UD-Q2_K_XL` passed 5/10. Q2 uniquely passed binary conversion and first-unique-character tasks, while IQ2 had no unique wins. See the [quant-triage summary](results/summaries/phase2-quant-triage.md) and its raw source records.

Decision: retain `UD-IQ2_XXS` as the provisional speed configuration and `UD-Q2_K_XL` as the provisional quality-oriented configuration. This small result does not establish general model quality, but it is enough to defer the 12.52 GiB `UD-Q3_K_XL` download. Phase 3 has now pinned the native runtime; the next gate is a repeated baseline for the two selected models.

## Phase 3 pinned native runtime

| Item | Observed value |
|---|---|
| Runtime | Official llama.cpp `b10448`, commit `ad1de39e0` |
| Binary target | Windows x64, CUDA 13.3 |
| Release archive validation | 537,670,077 bytes total; both SHA-256 values matched |
| Device | `CUDA0` — NVIDIA GeForce RTX 4070 Ti |
| Layer placement | 66/66 layers offloaded to GPU |
| Context / slots | 4,096 / 1 |
| KV cache | Q8 K and V; 136.00 MiB CUDA buffer |
| CUDA model / recurrent / compute buffers | 7,974.14 / 149.62 / 37.27 MiB |
| Loaded VRAM snapshot | 8,944 MiB used / 3,051 MiB free |
| Network scope | `127.0.0.1:8090`, localhost-only CORS |
| Native smoke checks | 3/3 passed |

See the [release manifest](environment/llama-cpp-b10448-manifest.json), [runtime record](environment/phase3-native-runtime-2026-08-15.json), [canonical raw result](results/raw/native-smoke-iq2-xxs-20260815T234835Z.json), and [Phase 3 checkpoint](results/summaries/phase3-native-checkpoint.md). The server-reported 37.57–43.81 tok/s values came from tiny smoke requests and are not a repeated baseline.

## Phase 4 repeated IQ2 baseline

| Metric | Mean | Sample SD | CV | Range |
|---|---:|---:|---:|---:|
| TTFT | 94.950 ms | 1.527 ms | 1.608% | 93.935–96.706 ms |
| Total latency | 6,001.517 ms | 6.525 ms | 0.109% | 5,996.504–6,008.894 ms |
| Prompt throughput | 935.648 tok/s | 0.441 | 0.047% | 935.266–936.131 |
| Generation throughput | 43.171 tok/s | 0.041 | 0.096% | 43.124–43.203 |

All three measured runs used 84 prompt tokens, generated 256 tokens with prompt caching disabled, reached 98% sampled GPU utilization, and peaked at 8,987 MiB VRAM used. Telemetry targeted 250 ms and achieved a 256.151 ms observed mean cadence.

See the [Phase 4 environment record](environment/phase4-iq2-baseline-2026-08-15.json), [raw result](results/raw/phase4-iq2-baseline-20260816T001913Z.json), and [interpretation checkpoint](results/summaries/phase4-iq2-baseline.md). The values apply only to this fixed workload and are not a Q2 comparison or quality result.

## Phase 5 Python harness

The new `qwen_bench` package uses only the Python standard library at runtime. It provides a loopback-only streaming client, monotonic TTFT timing, NVIDIA and Windows process telemetry, append-only writes, summary calculations, a Draft 2020-12 result schema, and cross-field semantic validation.

```powershell
.\scripts\setup_python.ps1
.\scripts\run_python_tests.ps1
.\scripts\run_phase5_harness.ps1
```

The controlled Phase 5 configuration performs one short 64-token request with no warm-up. This validates the software path and is explicitly not comparable to the repeated 256-token Phase 4 baseline.

The canonical run completed from harness commit `b0481d4`, retained 7 telemetry samples, and passed all 12 validation flags. It observed 43.479 generation tok/s, 87.340 ms TTFT, and 1,536.353 ms total latency; these single-run values are diagnostic only.

See the [Python environment record](environment/phase5-python-runtime-2026-08-15.json), [canonical raw result](results/raw/phase5-python-iq2-smoke-20260816T005922932894Z-a280beda.json), [formal result schema](schemas/benchmark-result.schema.json), and [Phase 5 checkpoint](results/summaries/phase5-python-harness-checkpoint.md).

## Phase 6 controlled quant comparison

Both quantizations used identical runtime, prompt, context, KV cache, sampling, and feature controls. Each received one excluded warm-up followed by three measured 256-token runs from a fresh server process.

| Metric | `UD-IQ2_XXS` | `UD-Q2_K_XL` | Q2 change vs IQ2 |
|---|---:|---:|---:|
| GPU layers | 66/66 | 66/66 | No CPU layer offload |
| Generation throughput | 43.643 tok/s | 38.030 tok/s | −12.861% |
| Total latency | 5,934.130 ms | 6,791.962 ms | +14.456% |
| Peak VRAM used | 8,976 MiB | 10,559 MiB | +1,583 MiB |
| Peak process private memory | 9.621 GiB | 11.167 GiB | +16.066% |

IQ2 was 14.759% faster than Q2 by the reciprocal decode-rate comparison and left approximately 1.55 GiB more VRAM headroom. At this phase, Q2 remained the quality-oriented candidate only because it passed 5/10 rather than 3/10 tasks in the separate Phase 2 triage; the later Phase 8 evaluation found no meaningful general-quality advantage.

See the [frozen protocol](environment/phase6-comparison-protocol-2026-08-15.json), [completed environment record](environment/phase6-comparison-2026-08-15.json), [human comparison](results/summaries/phase6-iq2-vs-q2.md), and [machine-readable derived result](results/summaries/phase6-iq2-vs-q2.json).

## Phase 7 context sensitivity

Each level used a fresh IQ2 server, one excluded warm-up, three measured repetitions, Q8 K/V cache, and a deterministic public synthetic prompt near 78% of the configured window.

| Metric | 4K | 8K | 16K |
|---|---:|---:|---:|
| Actual prompt tokens | 3,231 | 6,423 | 12,831 |
| Prompt throughput | 1,202.952 tok/s | 1,187.733 tok/s | 1,155.757 tok/s |
| TTFT | 2.693 s | 5.418 s | 11.119 s |
| Generation throughput | 41.124 tok/s | 40.522 tok/s | 39.201 tok/s |
| Peak VRAM used | 9,028 MiB | 9,182 MiB | 9,488 MiB |
| Minimum VRAM free | 2,967 MiB | 2,813 MiB | 2,507 MiB |

From 4K to 16K, decode throughput declined 4.676% and peak VRAM rose by 460 MiB. The 16K level passed the predeclared practical thresholds of at least 1,024 MiB VRAM headroom, no more than 30 seconds mean TTFT, and at least 30 generation tok/s.

See the [Phase 7 protocol](environment/phase7-context-protocol-2026-08-15.json), [completed environment record](environment/phase7-context-2026-08-15.json), [context-sensitivity summary](results/summaries/phase7-context-sensitivity.md), and [machine-readable comparison](results/summaries/phase7-context-sensitivity.json).

## Phase 8 objective quality evaluation

Each quant received the same 24 new tasks once under identical 4K, one-slot, cache-off, thinking-off controls. Exact and semantic-JSON graders were committed before measurement, raw answers were retained, and both records were independently re-graded from the committed suite.

| Quant | Overall | Arithmetic | Logic | Python trace | Structured output | Text/data |
|---|---:|---:|---:|---:|---:|---:|
| `UD-Q2_K_XL` | 10/24 | 0/5 | 2/5 | 1/5 | 5/5 | 2/4 |
| `UD-IQ2_XXS` | 9/24 | 0/5 | 2/5 | 1/5 | 4/5 | 2/4 |

Only five tasks were discordant: Q2 won three and IQ2 won two. The exact paired p-value was 1.0, so the observed one-task Q2 lead is descriptive only. Exact grading also measures format adherence—extra prose, wrong decimal formatting, or fenced JSON fails without partial credit.

The first Q2 attempt exposed a pre-write empty-answer preservation bug. Its 24 server completions and local log hash are disclosed, but it has no usable score. A narrow amendment separated request completion from answer correctness, added two regression tests, and froze the correction before a fresh Q2 restart; prompts, expected answers, graders, and model controls did not change.

See the [original protocol](environment/phase8-quality-protocol-2026-08-15.json), [protocol amendment](environment/phase8-quality-protocol-amendment-2026-08-15.json), [completed environment record](environment/phase8-quality-2026-08-15.json), [human summary](results/summaries/phase8-quality-comparison.md), and [machine-readable comparison](results/summaries/phase8-quality-comparison.json).

## Phase 9 IQ2 in-model MTP

The isolated MTP experiment used two greedy 256-token workloads, one excluded warm-up, and five measured repetitions per state from fresh 4K IQ2 processes.

| Workload | MTP off | MTP on | Speed change | Draft acceptance | Peak VRAM change | Exact output match |
|---|---:|---:|---:|---:|---:|---:|
| Prose | 42.152 tok/s | 62.083 tok/s | +47.284% | 55.187% | +568 MiB | 0/5 |
| Python code | 42.414 tok/s | 81.711 tok/s | +92.651% | 90.110% | +554 MiB | 5/5 |

The code response hashes matched across states. The prose was deterministic within each state but diverged at generated token 16, so this build's MTP path is not treated as a transparent accelerator. Keep MTP off by default; consider it only as an opt-in mode after workload-specific correctness testing.

See the [frozen protocol](environment/phase9-mtp-protocol-2026-08-15.json), [completed environment record](environment/phase9-mtp-2026-08-15.json), [human summary](results/summaries/phase9-mtp-comparison.md), and [machine-readable comparison](results/summaries/phase9-mtp-comparison.json).

## Phase 13 IQ4_XS hybrid-offload study

Phase 13 asks whether the possible quality benefit of a higher-bit quant is worth CPU/GPU hybrid-offload cost on this 12GB GPU. It deliberately separates configured context capacity from actual prompt length and uses community Q4 results only as motivation, not as comparable evidence.

The first two gates are versioned before measurement:

- the [artifact manifest](environment/phase13-iq4-xs-download-manifest.json) pins the immutable revision, exact size, SHA-256, and ignored local destination;
- the [preflight](environment/phase13-iq4-xs-preflight-2026-08-16.json) records storage, hardware, runtime, and clean-GPU requirements;
- the [protocol](environment/phase13-iq4-xs-protocol-2026-08-16.json) freezes the practical 4K offload frontier before later K/V-cache, active-context, MTP, and quality stages.

The offload frontier begins at 25 requested GPU layers, uses Q8 K/V and MTP off, and requires a successful short request, exact startup-log placement evidence, and at least 1,024 MiB post-request VRAM headroom. Frontier probes are capability and placement evidence—not repeated performance benchmarks.

The completed frontier selected 45/66 layers; 46/66 still ran but left only 856 MiB free and therefore missed the frozen safety gate. At the selected placement, the repeated IQ4_XS baseline averaged 5.977 generation tok/s with 0.098% CV. The matched Phase 6 IQ2 operating point was 7.302× faster, but it also fully offloaded 66/66 layers. See the [frontier](results/summaries/phase13-offload-frontier.md) and [repeated baseline](results/summaries/phase13-iq4-xs-4k-baseline.md). Quality, Q4 K/V, active-context, and MTP conclusions remain open.

The Stage 13D cache pair found Q4_0 reduced direct target K/V buffers by 64 MiB (47.059%) at 4K while generation changed only −0.201%. Q4_0 and Q8_0 produced different deterministic responses, so Q4_0 is an active-context candidate—not a transparent default replacement. See the [K/V comparison](results/summaries/phase13-iq4-xs-kv-cache.md).
