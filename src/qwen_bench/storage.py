"""Append-only JSON result storage."""

from __future__ import annotations

import json
import os
import re
from pathlib import Path
from typing import Any


class ResultExistsError(FileExistsError):
    """Raised when a result filename is already occupied."""


def write_result_exclusive(output_directory: Path, run_id: str, record: dict[str, Any]) -> Path:
    """Serialize and create ``<run_id>.json`` without ever overwriting a file."""

    if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._-]{0,199}", run_id):
        raise ValueError("Run ID is not a safe filename stem.")
    output_directory.mkdir(parents=True, exist_ok=True)
    output_path = output_directory / f"{run_id}.json"
    payload = json.dumps(record, indent=2, ensure_ascii=False) + "\n"
    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL
    try:
        descriptor = os.open(output_path, flags, 0o644)
    except FileExistsError as error:
        raise ResultExistsError(f"Refusing to overwrite result: {output_path.name}") from error
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8", newline="\n") as stream:
            stream.write(payload)
            stream.flush()
            os.fsync(stream.fileno())
    except Exception:
        # Preserve the exclusive file as failure evidence instead of silently
        # deleting or replacing a partially written result.
        raise
    return output_path
