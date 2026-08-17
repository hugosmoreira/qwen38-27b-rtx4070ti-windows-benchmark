# Phase 13 64K/Q4_0 capacity frontier

This diagnostic allocated a 65,536-token context with Q4_0 target K/V and used one short 38-token prompt plus 64 generated tokens per fresh process. Its purpose was to select one fixed layer placement for the later active-prompt ladder.

| GPU layers | VRAM used after request | VRAM free after request | Short-request decode | Practical |
|---:|---:|---:|---:|---:|
| 25/66 | 7,487 MiB | 4,508 MiB | 3.45 tok/s | Yes |
| 33/66 | 9,281 MiB | 2,714 MiB | 4.16 tok/s | Yes |
| 41/66 | 11,077 MiB | 918 MiB | 5.24 tok/s | No—headroom |
| 37/66 | 10,164 MiB | 1,831 MiB | 4.64 tok/s | Yes |
| 39/66 | 10,640 MiB | 1,355 MiB | 4.91 tok/s | Yes |
| 40/66 | 10,852 MiB | 1,143 MiB | 5.07 tok/s | Yes |

All six placements started, completed the request, and matched their startup logs. There was no OOM. Under the frozen 1,024 MiB rule, **40/66** is selected and **41/66** is the first non-practical placement.

This does not validate a long prompt: the probe used only 38 prompt tokens. The later ladder fixes 40/66 across all contexts and reserves a near-64K claim for at least 60,000 observed prompt tokens.

Source: [`phase13-iq4-offload-frontier-65536-q4-0-20260817T040527025Z.json`](../raw/phase13-iq4-offload-frontier-65536-q4-0-20260817T040527025Z.json), SHA-256 `dfef4f5292b16bddcdf2784cf2de867d7fe4015b9589a1afda40b9b9a2003d17`.
