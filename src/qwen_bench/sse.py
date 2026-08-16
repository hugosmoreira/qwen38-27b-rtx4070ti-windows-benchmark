"""Server-Sent Events parsing for OpenAI-compatible streaming responses."""

from __future__ import annotations

import json
from collections.abc import Iterable, Iterator
from typing import Any


class SSEProtocolError(ValueError):
    """Raised when a non-terminal SSE data payload is not valid JSON."""


def iter_sse_json(lines: Iterable[bytes | str]) -> Iterator[dict[str, Any]]:
    """Yield JSON objects from SSE ``data:`` lines until ``[DONE]``.

    Empty lines, comments, event metadata, and other fields are ignored. The
    llama.cpp endpoint emits one JSON object per data line, so multi-line SSE
    data fields are intentionally outside this harness's accepted protocol.
    """

    for raw_line in lines:
        line = raw_line.decode("utf-8") if isinstance(raw_line, bytes) else raw_line
        line = line.rstrip("\r\n")
        if not line.startswith("data:"):
            continue
        payload = line[5:].lstrip()
        if not payload:
            continue
        if payload == "[DONE]":
            return
        try:
            value = json.loads(payload)
        except json.JSONDecodeError as error:
            raise SSEProtocolError(f"Invalid JSON in SSE data field at character {error.pos}.") from error
        if not isinstance(value, dict):
            raise SSEProtocolError("SSE JSON data must be an object.")
        yield value
