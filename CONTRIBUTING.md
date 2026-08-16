# Contributing

Contributions that improve reproducibility, validation, Windows compatibility, or interpretation are welcome. This is an evidence repository: benchmark claims need inspectable raw data and a controlled protocol, not only screenshots or headline token rates.

## Before opening an issue

- Search existing issues and result summaries.
- Remove credentials, local user paths, proprietary prompts, and model weights.
- Identify the exact Git commit, model revision, runtime build, and hardware involved.
- Distinguish a harness defect from a model-quality observation.

Use the harness-bug template for software defects and the reproduction template for new measurements or methodology differences. Security-sensitive reports should follow [SECURITY.md](SECURITY.md), not a public issue.

## Development setup

The package supports CPython 3.11 through 3.14 and has no runtime dependencies. On Windows PowerShell:

```powershell
.\scripts\setup_python.ps1
.\scripts\run_python_tests.ps1
```

For direct commands:

```powershell
$env:PYTHONPATH = (Resolve-Path .\src).Path
.\.venv\Scripts\python.exe -m qwen_bench --help
.\.venv\Scripts\python.exe -m qwen_bench release-audit --repository-root .
```

## Change rules

1. Keep the Python runtime path standard-library only unless a dependency is justified and reviewed.
2. Add or update tests for parsing, validation, grading, statistics, or comparison changes.
3. Commit protocols, prompts, graders, and calculations before generating evidence they will evaluate.
4. Write raw results append-only with unique names. Never replace an earlier run silently.
5. Classify every tracked raw record in `release/v0.1.0-manifest.json` as canonical, superseded, or diagnostic.
6. Preserve failed and superseded runs when they explain a correction or decision.
7. Keep performance claims separate from quality claims unless both have independent evidence.
8. Do not commit GGUF files, caches, runtime archives, authentication material, or private learning documents.

## Pull requests

Keep pull requests focused. Explain controlled variables, deviations, and interpretation limits. Include the commands used for validation and link each numerical claim to raw or derived evidence. GPU measurements are not required for ordinary software changes, and CI must not be presented as hardware reproduction.

By contributing, you confirm that you have the right to submit the material under the repository's [Apache License 2.0](LICENSE).
