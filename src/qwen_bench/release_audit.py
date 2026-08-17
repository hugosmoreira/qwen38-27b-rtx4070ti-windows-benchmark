"""Clean-clone and evidence checks for the public release candidate."""

from __future__ import annotations

import os
import re
import subprocess
from pathlib import Path
from typing import Any
from urllib.parse import unquote

from qwen_bench.config import load_json_object
from qwen_bench.quality_result_validation import validate_quality_result
from qwen_bench.result_validation import validate_result


_MARKDOWN_LINK = re.compile(
    r"!?\[[^\]]*\]\((?P<target><[^>]+>|[^)\s]+)(?:\s+\"[^\"]*\")?\)"
)
_TEXT_SUFFIXES = {
    "",
    ".cff",
    ".gitignore",
    ".gitattributes",
    ".editorconfig",
    ".json",
    ".md",
    ".ps1",
    ".py",
    ".toml",
    ".txt",
    ".yaml",
    ".yml",
}
_ABSOLUTE_LOCAL_PATHS = ("C:\\Users\\", "E:\\CODEX\\")


def audit_repository(repository_root: Path, *, strict: bool = False) -> dict[str, Any]:
    root = repository_root.resolve()
    manifest_path = root / "release" / "v0.1.0-manifest.json"
    manifest = load_json_object(manifest_path)
    tracked = _tracked_files(root)
    tracked_set = set(tracked)
    issues: list[str] = []
    warnings: list[str] = []
    checks: dict[str, bool] = {}

    technical_required = set(manifest["technical_required_files"])
    missing_technical = sorted(technical_required - tracked_set)
    checks["technical_release_files_tracked"] = not missing_technical
    issues.extend(f"required technical file is not tracked: {path}" for path in missing_technical)

    forbidden_paths = set(manifest["artifact_policy"]["forbidden_private_paths"])
    forbidden_extensions = {
        str(value).lower() for value in manifest["artifact_policy"]["forbidden_extensions"]
    }
    forbidden_names = set(manifest["artifact_policy"]["forbidden_exact_names"])
    artifact_violations = [
        path
        for path in tracked
        if path in forbidden_paths
        or Path(path).suffix.lower() in forbidden_extensions
        or Path(path).name in forbidden_names
    ]
    checks["no_forbidden_artifacts_tracked"] = not artifact_violations
    issues.extend(f"forbidden public artifact is tracked: {path}" for path in artifact_violations)

    artifact_policy = manifest["artifact_policy"]
    oversized = [
        (path, _maximum_size_for_path(path, artifact_policy))
        for path in tracked
        if (root / path).stat().st_size > _maximum_size_for_path(path, artifact_policy)
    ]
    checks["tracked_files_within_size_limit"] = not oversized
    issues.extend(
        f"tracked file exceeds {maximum_bytes} bytes: {path}"
        for path, maximum_bytes in oversized
    )

    json_issues = _validate_all_json(root, tracked)
    checks["tracked_json_parses_without_duplicate_keys"] = not json_issues
    issues.extend(json_issues)

    link_issues = _validate_markdown_links(root, tracked)
    checks["repository_relative_markdown_links_resolve"] = not link_issues
    issues.extend(link_issues)

    local_path_issues = _scan_absolute_local_paths(root, tracked)
    checks["no_absolute_local_paths_in_public_text"] = not local_path_issues
    issues.extend(local_path_issues)

    coverage_issues = _validate_raw_coverage(manifest, tracked)
    checks["all_raw_records_classified_once"] = not coverage_issues
    issues.extend(coverage_issues)

    evidence_issues, evidence_counts = _validate_canonical_evidence(root, manifest)
    checks["canonical_evidence_validates"] = not evidence_issues
    issues.extend(evidence_issues)

    ignored_issues = _validate_private_ignores(root, forbidden_paths)
    checks["private_learning_paths_ignored"] = not ignored_issues
    issues.extend(ignored_issues)

    placeholders = _find_publication_placeholders(root, manifest)
    pending = list(manifest.get("pending_owner_decisions", []))
    if placeholders:
        warnings.extend(f"publication placeholder remains: {value}" for value in placeholders)
    if pending:
        warnings.extend(f"owner decision remains: {value}" for value in pending)

    if strict:
        strict_required = set(manifest["strict_release_required_files"])
        missing_strict = sorted(strict_required - tracked_set)
        checks["strict_release_metadata_tracked"] = not missing_strict
        issues.extend(f"strict release file is not tracked: {path}" for path in missing_strict)
        checks["owner_decisions_resolved"] = not pending
        issues.extend(f"owner decision is unresolved: {value}" for value in pending)
        checks["publication_placeholders_resolved"] = not placeholders
        issues.extend(f"publication placeholder remains: {value}" for value in placeholders)

    return {
        "schema_version": "release-audit-1.0",
        "candidate_version": manifest["candidate_version"],
        "strict": strict,
        "status": "passed" if not issues else "failed",
        "tracked_files": len(tracked),
        "canonical_evidence": evidence_counts,
        "checks": checks,
        "issues": issues,
        "warnings": warnings,
    }


def _tracked_files(root: Path) -> list[str]:
    creation_flags = subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0
    completed = subprocess.run(
        ["git", "-c", f"safe.directory={root.as_posix()}", "ls-files", "-z"],
        cwd=root,
        capture_output=True,
        check=True,
        timeout=30.0,
        creationflags=creation_flags,
    )
    return sorted(
        value.decode("utf-8") for value in completed.stdout.split(b"\0") if value
    )


def _maximum_size_for_path(path: str, artifact_policy: dict[str, Any]) -> int:
    default_maximum = int(artifact_policy["maximum_tracked_file_bytes"])
    raw_result_maximum = int(
        artifact_policy.get("maximum_raw_result_file_bytes", default_maximum)
    )
    normalized = path.replace("\\", "/")
    if normalized.startswith("results/raw/") and Path(normalized).suffix.lower() == ".json":
        return raw_result_maximum
    return default_maximum


def _validate_all_json(root: Path, tracked: list[str]) -> list[str]:
    issues: list[str] = []
    for relative in tracked:
        if Path(relative).suffix.lower() != ".json":
            continue
        try:
            load_json_object(root / relative)
        except ValueError as error:
            issues.append(f"invalid tracked JSON {relative}: {error}")
    return issues


def _validate_markdown_links(root: Path, tracked: list[str]) -> list[str]:
    root = root.resolve()
    issues: list[str] = []
    for relative in tracked:
        if Path(relative).suffix.lower() != ".md":
            continue
        source = root / relative
        text = source.read_text(encoding="utf-8")
        for match in _MARKDOWN_LINK.finditer(text):
            target = match.group("target").strip("<>")
            if target.startswith(("http://", "https://", "mailto:", "#")):
                continue
            without_anchor = target.split("#", 1)[0]
            if not without_anchor:
                continue
            resolved = (source.parent / unquote(without_anchor)).resolve()
            try:
                resolved.relative_to(root)
            except ValueError:
                issues.append(f"Markdown link escapes repository: {relative} -> {target}")
                continue
            if not resolved.exists():
                issues.append(f"broken repository-relative Markdown link: {relative} -> {target}")
    return issues


def _scan_absolute_local_paths(root: Path, tracked: list[str]) -> list[str]:
    issues: list[str] = []
    for relative in tracked:
        path = root / relative
        if path.suffix.lower() not in _TEXT_SUFFIXES and path.name not in _TEXT_SUFFIXES:
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        for marker in _ABSOLUTE_LOCAL_PATHS:
            if marker.lower() in text.lower():
                issues.append(f"absolute local path marker {marker!r} found in {relative}")
    return issues


def _validate_raw_coverage(manifest: dict[str, Any], tracked: list[str]) -> list[str]:
    classified: list[str] = []
    for values in manifest["canonical_evidence"].values():
        classified.extend(str(value) for value in values)
    classified.extend(str(value["path"]) for value in manifest["noncanonical_evidence"])
    duplicates = sorted({value for value in classified if classified.count(value) > 1})
    tracked_raw = sorted(
        value for value in tracked if value.startswith("results/raw/") and value.endswith(".json")
    )
    issues = [f"raw evidence is classified more than once: {path}" for path in duplicates]
    issues.extend(
        f"tracked raw evidence is not classified: {path}"
        for path in sorted(set(tracked_raw) - set(classified))
    )
    issues.extend(
        f"manifest classifies an untracked raw file: {path}"
        for path in sorted(set(classified) - set(tracked_raw))
    )
    return issues


def _validate_canonical_evidence(
    root: Path, manifest: dict[str, Any]
) -> tuple[list[str], dict[str, int]]:
    issues: list[str] = []
    counts: dict[str, int] = {}
    for kind, paths in manifest["canonical_evidence"].items():
        counts[kind] = len(paths)
        for relative in paths:
            record = load_json_object(root / relative)
            if kind == "benchmark_result":
                validation = validate_result(record)
            elif kind == "quality_result":
                suite = load_json_object(root / str(record.get("prompt_suite", "")))
                validation = validate_quality_result(record, suite)
            elif kind == "legacy_json":
                validation = []
            else:
                validation = [f"unsupported canonical evidence kind {kind!r}"]
            issues.extend(f"canonical evidence {relative}: {value}" for value in validation)
    return issues, counts


def _validate_private_ignores(root: Path, private_paths: set[str]) -> list[str]:
    creation_flags = subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0
    issues: list[str] = []
    for relative in sorted(private_paths):
        completed = subprocess.run(
            [
                "git",
                "-c",
                f"safe.directory={root.as_posix()}",
                "check-ignore",
                "--quiet",
                "--",
                relative,
            ],
            cwd=root,
            check=False,
            timeout=10.0,
            creationflags=creation_flags,
        )
        if completed.returncode != 0:
            issues.append(f"private path is not ignored: {relative}")
    return issues


def _find_publication_placeholders(root: Path, manifest: dict[str, Any]) -> list[str]:
    remaining: list[str] = []
    for entry in manifest.get("publication_placeholders", []):
        path = root / str(entry["path"])
        text = str(entry["text"])
        if text in path.read_text(encoding="utf-8"):
            remaining.append(f"{entry['path']}: {text}")
    return remaining
