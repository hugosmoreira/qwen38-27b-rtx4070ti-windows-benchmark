# Project Execution Plan

## Current status

- Phase 0 completed on 2026-08-15.
- Phase 1 completed on 2026-08-15 with the pinned `UD-IQ2_XXS` model and a 3/3 passing proof-of-life suite.
- Phase 2 is complete. `UD-IQ2_XXS` is the provisional speed configuration and `UD-Q2_K_XL` is the provisional quality-oriented configuration after a controlled 3/10 versus 5/10 quant-triage result. `UD-Q3_K_XL` is deferred.
- Phase 3 completed on 2026-08-15 with official llama.cpp `b10448`: both release archives were checksum-validated, CUDA0 startup logs reported 66/66 layers offloaded to the RTX 4070 Ti, and the native OpenAI-compatible smoke suite passed 3/3.
- Phase 4 completed on 2026-08-15. One excluded warm-up and three measured 256-token IQ2 repetitions produced 43.171 generation tok/s mean with 0.096% CV, while streaming TTFT averaged 94.950 ms with 1.608% CV.
- Phase 5 completed on 2026-08-15. The standard-library Python harness passed 23 offline tests, then one committed end-to-end smoke run passed all 12 validation flags and retained raw streaming plus telemetry evidence.
- Phase 6 completed on 2026-08-15. Under frozen 4K controls, IQ2 averaged 43.643 generation tok/s versus 38.030 for Q2 and used 1,583 MiB less peak VRAM. Both configurations reported 66/66 GPU layers, so this is not a CPU layer-offload comparison.

## Objective

Measure whether Qwen3.8-27B is practical on a Windows desktop with an RTX 4070 Ti 12GB and 64 GB system RAM. The primary experiment compares lower-bit, mostly GPU-resident inference with higher-bit inference that requires CPU/system-RAM offload.

## Scope

Version 0.1 includes:

- native Windows inference;
- Unsloth Desktop for the first proof of life;
- a pinned Windows CUDA build of llama.cpp for reproducible measurements;
- 2-bit, 3-bit, and possibly 4-bit GGUF comparisons;
- performance, memory, context, and small quality evaluations;
- a public GitHub repository;
- a Hugging Face Community performance report;
- a concise LinkedIn/X summary after results exist.

Version 0.1 excludes:

- Qwen3.8-27B fine-tuning;
- downloading the 2.4T model;
- claiming 262K or 1M context is practical on this PC;
- uploading or redistributing GGUF model weights;
- presenting one run as a definitive benchmark;
- treating RTX 5090 or RTX 4090 results as predictions for this machine.

## Execution rules

1. Work one phase at a time.
2. End each phase with an inspection checkpoint.
3. State the exact size and destination before a multi-gigabyte download.
4. Record errors before changing direction.
5. Keep raw measurements append-only.
6. Change one experimental factor at a time.
7. Separate performance conclusions from quality conclusions.
8. Review public text before any GitHub or Hugging Face submission.

## Phase gates

### Phase 0 — Repository and environment

- Initialize the local Git repository.
- Add professional project documentation and a reproducible environment snapshot.
- Record the verified environment.
- Prepare folders and ignore rules.
- Do not download a model.

Exit condition: the repository is self-explanatory and the first proposed download is documented.

### Phase 1 — First successful Unsloth Desktop run

- Download `UD-IQ2_XXS` after approval.
- Start text-only at 4,096 context and one slot.
- Disable Preserve Thinking, tools, web search, code execution, and vision.
- Record actual app settings, VRAM, RAM, offload, and reported speed.

Exit condition: several prompts complete reliably and the settings are recorded.

Status: completed on 2026-08-15. Evidence is stored in `environment/phase1-unsloth-runtime-2026-08-15.json` and `results/raw/phase1-smoke-20260815T225920Z.json`.

### Phase 2 — Practical quant selection

Test one new quant at a time in this order:

1. `UD-IQ2_XXS`
2. `UD-Q2_K_XL`
3. `UD-Q3_K_XL`
4. `UD-Q4_K_XL`, only if earlier results justify the download

Exit condition: select one speed-oriented and one quality-oriented configuration.

Status: completed on 2026-08-15. Selected `UD-IQ2_XXS` for speed and `UD-Q2_K_XL` as the quality-oriented candidate. The ten-task triage is selection evidence, not the final quality evaluation.

### Phase 3 — Pinned llama.cpp runtime

- Select an official Windows x64 CUDA release.
- Verify checksums when available.
- Verify startup logs report CUDA rather than CPU-only or unintended Vulkan execution.
- Pin all material flags.

Exit condition: the selected model runs through a local OpenAI-compatible server.

Status: completed on 2026-08-15. The canonical runtime record is `environment/phase3-native-runtime-2026-08-15.json`, and the successful raw API result is `results/raw/native-smoke-iq2-xxs-20260815T234835Z.json`.

### Phase 4 — Trustworthy baseline

- One warm-up run.
- At least three measured repetitions.
- Record prompt processing, generation, TTFT, latency, VRAM, RAM, CPU, GPU, context, KV cache, and offload.

Exit condition: repeated runs are saved in a machine-readable format and variation is understood.

Status: completed on 2026-08-15 for the IQ2 baseline. The canonical raw result is `results/raw/phase4-iq2-baseline-20260816T001913Z.json`; the derived checkpoint is `results/summaries/phase4-iq2-baseline.md`. Q2 comparison remains Phase 6.

### Phase 5 — Benchmark harness

- Install a supported Python version in an isolated environment.
- Implement the API client, timing, telemetry, schemas, and unique result files.
- Add tests for our own calculations and parsing.

Exit condition: one end-to-end automated run passes and retains raw output.

Status: completed on 2026-08-15. The harness provenance commit is `b0481d4`; the canonical raw result is `results/raw/phase5-python-iq2-smoke-20260816T005922932894Z-a280beda.json`, and the checkpoint is `results/summaries/phase5-python-harness-checkpoint.md`.

### Phase 6 — Quant/offload comparison

- Compare the chosen speed and quality configurations.
- Hold runtime, prompt, context, KV cache, thinking, sampling, MTP, and vision settings constant.

Exit condition: the performance tradeoff is reproducible.

Status: completed on 2026-08-15. Both canonical records passed structural and semantic validation with one excluded warm-up and three measured repetitions. The protocol commit is `94a2735`; the derived checkpoint is `results/summaries/phase6-iq2-vs-q2.md`.

### Phase 7 — Context sensitivity

- Test 4K, 8K, and 16K contexts.
- Preserve OOM and failed configurations.

Exit condition: identify the largest sensible local context for the selected quant.

### Phase 8 — Small quality evaluation

- Use 15–30 inspectable tasks.
- Favor tests, JSON Schema, exact constraints, and pass@1.
- Preserve raw responses.

Exit condition: performance and quality can be discussed separately with evidence.

### Phase 9 — Optional isolated experiments

- MTP on versus off.
- Vision with `mmproj`.
- Standard `Q4_K_M` versus `UD-Q4_K_XL`.
- Unsloth Desktop versus native llama.cpp convenience and defaults.

These experiments must not silently change the baseline.

### Phase 10 — GitHub study release

- Complete README, methodology, results, limitations, and charts.
- Tag a versioned release only after review.
- Never commit model weights.

### Phase 11 — Hugging Face Community report

- Draft `reports/huggingface-community-report.md`.
- Link every headline number to the public GitHub results.
- Post to `unsloth/Qwen3.8-27B-GGUF` only after explicit approval.

### Phase 12 — Public communication

- Publish an evidence-first LinkedIn post.
- Publish a concise X/Twitter thread.
- Optionally share with local-LLM communities for methodology feedback.

## Success criteria

The project succeeds if another technical reader can:

1. understand exactly what was tested;
2. reproduce the benchmark on comparable Windows hardware;
3. distinguish measured facts from interpretation;
4. inspect raw results and our calculation code;
5. understand why a configuration won or failed;
6. learn from the documented engineering decisions.

## Authoritative external sources

- Qwen model: https://huggingface.co/Qwen/Qwen3.8-27B
- Unsloth guide: https://unsloth.ai/docs/models/qwen3.8
- GGUF repository: https://huggingface.co/unsloth/Qwen3.8-27B-GGUF
- Unsloth requirements: https://unsloth.ai/docs/get-started/fine-tuning-for-beginners/unsloth-requirements
- llama.cpp: https://github.com/ggml-org/llama.cpp
- Hugging Face Community workflow: https://huggingface.co/docs/hub/en/repositories-pull-requests-discussions

Recheck these sources before installations and large downloads because the model and supporting tooling are new.
