"""Deterministic public synthetic-context fixtures."""

from __future__ import annotations

import hashlib
from typing import Any


NUMBERED_RECORDS_GENERATOR = "numbered-records-v1"
_NUMBERED_RECORD_LINE = (
    "Record {index:05d}: amber cedar delta frost harbor juniper lunar meadow "
    "quartz river summit violet.\n"
)


def build_user_content(workload: dict[str, Any]) -> str:
    """Return the exact user content, expanding a supported fixture when present."""

    instruction = str(workload["user"])
    fixture = workload.get("synthetic_context")
    if fixture is None:
        return instruction
    if fixture.get("generator") != NUMBERED_RECORDS_GENERATOR:
        raise ValueError("Unsupported synthetic-context generator.")
    record_count = int(fixture["record_count"])
    records = "".join(
        _NUMBERED_RECORD_LINE.format(index=index)
        for index in range(1, record_count + 1)
    )
    return f"{records}\n{instruction}"


def synthetic_context_metadata(workload: dict[str, Any]) -> dict[str, str | int]:
    """Describe the generated input with scalar fields safe for result metadata."""

    fixture = workload.get("synthetic_context")
    if fixture is None:
        return {}
    content = build_user_content(workload)
    encoded = content.encode("utf-8")
    return {
        "synthetic_context_generator": str(fixture["generator"]),
        "synthetic_context_record_count": int(fixture["record_count"]),
        "synthetic_context_utf8_bytes": len(encoded),
        "synthetic_context_user_sha256": hashlib.sha256(encoded).hexdigest(),
    }
