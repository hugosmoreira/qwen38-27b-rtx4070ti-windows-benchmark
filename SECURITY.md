# Security policy

## Supported versions

Security fixes will target the latest published `0.1.x` release and the current `main` branch after the repository is public.

## Reporting a vulnerability

Do not disclose a suspected vulnerability in a public issue. After publication, use GitHub private vulnerability reporting for this repository. Before publication, report it privately to the repository owner through an already established contact channel.

Useful reports identify the affected commit, entry point, expected security property, impact, and a minimal reproduction that contains no real credentials or private data.

## In scope

- loopback and URL validation bypasses;
- unsafe path resolution, traversal, or overwrite behavior;
- credential or local-secret exposure;
- command or argument injection in the PowerShell wrappers;
- unsafe parsing of result, prompt, manifest, or configuration files;
- release-audit bypasses that could publish private or oversized artifacts.

Model hallucinations, prompt-injection behavior inside an intentionally local model session, benchmark score disagreements, and upstream runtime vulnerabilities are not automatically vulnerabilities in this harness. They may still deserve a normal issue or an upstream report.

Never include model weights, desktop secrets, API keys, private prompts, or unrelated local files in a report.
