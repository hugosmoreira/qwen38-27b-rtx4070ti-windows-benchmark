# Phase 9 — IQ2 in-model MTP experiment

## Decision

Keep MTP **off by default** for this pinned runtime. `draft-mtp` accelerated both tested 256-token workloads, but the deterministic prose output diverged from the MTP-off control at generated token index 16. The Python-code output matched exactly. MTP is therefore an opt-in experimental accelerator that needs workload-specific correctness regression tests, not a transparent default optimization.

## Controlled result

All configurations used `UD-IQ2_XXS`, llama.cpp `b10448`, CUDA0, 4K context, one slot, 66/66 target layers on the GPU, Q8 target K/V, cache off, thinking off, temperature 0, and seed 42. MTP used the embedded NextN layer with `draft-mtp`, draft depth two, and an F16 draft K/V cache. Each state received one excluded warm-up and five measured repetitions from a fresh server process.

| Workload | MTP off tok/s | MTP on tok/s | Speed change | Draft acceptance | Latency change | Peak VRAM change | Exact output match |
|---|---:|---:|---:|---:|---:|---:|---:|
| Prose | 42.152 | 62.083 | +47.284% | 55.187% | −31.588% | +568 MiB | 0/5 |
| Python code | 42.414 | 81.711 | +92.651% | 90.110% | −47.213% | +554 MiB | 5/5 |

Generation-speed CV remained below 0.13% for all four states. MTP increased mean TTFT by 2.139 ms for prose and 4.812 ms for code, while reducing total 256-token latency by 1.940 seconds and 2.887 seconds respectively. Sampled process private memory increased by about 1.21 GiB in both workloads.

## Acceptance explains why workload matters

The prose runs accepted 665 of 1,205 drafted tokens (55.187%). The code runs accepted 820 of 910 (90.110%). The higher, highly repetitive code acceptance coincided with the larger speedup. This relationship is descriptive for two workloads; it is not a general performance model.

## Output-equivalence finding

Every measured response was internally deterministic within its own state. Code used the same UTF-8 SHA-256 in all ten measured outputs across both states: `5106ec441adbb47779beacc5b67b4af87118792ad2ad8bd47ce2de138efcd96c`.

Prose was internally deterministic but differed between states. MTP-off used `b1bbe27cc45eff8f048daf6eb0cccbbaca99a089b95bb8082f47ca80afa3c6ab`; MTP-on used `042cf50125425abe3bf40b85d6b44ab10a7e85de2d5d2378b7a9c8500790aeea`. The first difference occurred at zero-based character 102 and generated token 16. Both outputs contained 256 completion tokens. Because the prose was not quality-graded, this proves an equivalence failure—not that one version was better or worse.

## Memory evidence

MTP startup added a 16 MiB CUDA draft KV buffer and a 31.50 MiB CUDA draft compute buffer and activated the embedded NextN tensors. The loaded GPU snapshot rose by about 560 MiB. During measured runs, sampled peak VRAM rose from 9,007 to 9,575 MiB for prose and from 9,021 to 9,575 MiB for code, leaving 2,420 MiB sampled free.

## Reproduction and audit

The frozen protocol commit is `e3c950f15407182e45de778071c9ff4c94dac7c6`. The four raw records pass independent structural and semantic validation, and the comparison command rejects control drift, missing draft activity, and invalid draft counters. The package passes 58 offline tests.

```powershell
$env:PYTHONPATH = Join-Path (Get-Location) 'src'
.\.venv\Scripts\python.exe -m qwen_bench mtp-compare `
    results/raw/phase9-mtp-off-prose-20260816T041445808671Z-76083f38.json `
    results/raw/phase9-mtp-on-prose-20260816T041603771264Z-9c3f8aca.json `
    results/raw/phase9-mtp-off-code-20260816T041809117916Z-bdba6559.json `
    results/raw/phase9-mtp-on-code-20260816T041709353404Z-221a5138.json
```

## Interpretation boundary

This is a two-workload compatibility and performance experiment on one machine. It does not establish MTP quality, correctness across arbitrary prompts, performance at other context sizes, or behavior in newer llama.cpp builds. Speed is reported per workload and is not pooled. Q3, Q4, vision, and Unsloth-versus-native experiments remain deferred.
