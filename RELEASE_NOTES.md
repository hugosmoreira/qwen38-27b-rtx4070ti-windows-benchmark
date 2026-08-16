# v0.1.0 release candidate

This release candidate packages an auditable Windows study of Qwen3.8-27B GGUF inference on an RTX 4070 Ti 12 GB. It includes the benchmark software, frozen protocols, prompts and graders, machine-readable environment records, canonical raw responses, derived comparisons, and explicit superseded evidence. Model weights and runtime archives are not included.

## Headline findings

- Both `UD-IQ2_XXS` and `UD-Q2_K_XL` fully offloaded 66/66 layers at 4K context.
- IQ2 averaged 43.643 generation tok/s versus 38.030 for Q2 and used 1,583 MiB less sampled peak VRAM.
- On 24 paired objective tasks, Q2 passed 10 and IQ2 passed 9; exact McNemar `p = 1.0` did not support a directional quality claim.
- IQ2 completed the tested 16K configuration with a 12,831-token prompt plus 128 generated tokens, 39.201 generation tok/s, and 2,507 MiB minimum sampled free VRAM.
- MTP increased throughput 47.284% for prose and 92.651% for code, but prose output diverged at generated token 16. MTP remains off by default.

## Reproduce and inspect

No GPU or model download is required to run the 61-test software suite, validate canonical Phase 5–9 records, check public links, and audit release boundaries. See [REPRODUCING.md](REPRODUCING.md).

## Publication state

This is still a local release candidate, but its strict local release gate has passed. Apache-2.0, Hugo Moreira's citation identity, the Code of Conduct contact, repository coordinates, and report URLs are finalized. Repository creation, push, tag creation, GitHub release publication, and Hugging Face posting still require explicit approval.

## Interpretation boundary

The results apply to one declared Windows machine, pinned model files, llama.cpp `b10448`, and the committed workloads. They do not establish general model quality, universal context capacity, or performance on other systems. Q3, Q4, vision, and Unsloth-versus-native convenience comparisons remain deferred.
