"""Standard-library client for the loopback llama.cpp HTTP server."""

from __future__ import annotations

import json
import time
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass
from typing import Any

from qwen_bench.sse import iter_sse_json


class ClientError(RuntimeError):
    """Raised for HTTP, protocol, or local safety failures."""


def require_loopback_uri(base_uri: str) -> str:
    parsed = urllib.parse.urlparse(base_uri)
    if parsed.scheme != "http" or parsed.hostname not in {"127.0.0.1", "localhost", "::1"}:
        raise ClientError("Benchmark server URI must use HTTP on a loopback host.")
    if parsed.username or parsed.password or parsed.query or parsed.fragment:
        raise ClientError("Benchmark server URI must not contain credentials, a query, or a fragment.")
    return base_uri.rstrip("/")


@dataclass(frozen=True)
class StreamResult:
    response_headers_ms: float
    time_to_first_content_token_ms: float | None
    total_latency_ms: float
    finish_reason: str | None
    content: str
    reasoning_content: str | None
    usage: dict[str, Any] | None
    timings: dict[str, Any] | None
    system_fingerprint: str | None


class LlamaCppClient:
    def __init__(self, base_uri: str, timeout_seconds: float = 600.0) -> None:
        self.base_uri = require_loopback_uri(base_uri)
        self.timeout_seconds = timeout_seconds

    def get_json(self, path: str) -> dict[str, Any]:
        request = urllib.request.Request(f"{self.base_uri}{path}", method="GET")
        try:
            with urllib.request.urlopen(request, timeout=min(self.timeout_seconds, 30.0)) as response:
                value = json.load(response)
        except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as error:
            raise ClientError(f"GET {path} failed: {type(error).__name__}.") from error
        if not isinstance(value, dict):
            raise ClientError(f"GET {path} returned a non-object JSON value.")
        return value

    def validate_server(
        self,
        *,
        model_alias: str,
        expected_context_size: int,
        expected_parallel_slots: int,
        expected_model_path: str,
    ) -> dict[str, Any]:
        health = self.get_json("/health")
        models = self.get_json("/v1/models")
        props = self.get_json("/props")

        model_ids = [item.get("id") for item in models.get("data", []) if isinstance(item, dict)]
        settings = props.get("default_generation_settings", {})
        checks = {
            "health_ok": health.get("status") == "ok",
            "model_alias_present": model_alias in model_ids,
            "context_size_matches": settings.get("n_ctx") == expected_context_size,
            "parallel_slots_match": props.get("total_slots") == expected_parallel_slots,
            "model_path_matches_manifest": _same_path(props.get("model_path"), expected_model_path),
        }
        if not all(checks.values()):
            failed = ", ".join(name for name, passed in checks.items() if not passed)
            raise ClientError(f"Server preflight validation failed: {failed}.")
        return {
            "status": "passed",
            "checks": checks,
            "served_model_alias": model_alias,
        }

    def stream_chat(self, body: dict[str, Any]) -> StreamResult:
        encoded = json.dumps(body, separators=(",", ":")).encode("utf-8")
        request = urllib.request.Request(
            f"{self.base_uri}/v1/chat/completions",
            data=encoded,
            method="POST",
            headers={"Content-Type": "application/json", "Accept": "text/event-stream"},
        )
        started_ns = time.perf_counter_ns()
        try:
            response = urllib.request.urlopen(request, timeout=self.timeout_seconds)
        except urllib.error.HTTPError as error:
            raise ClientError(f"Chat request returned HTTP {error.code}.") from error
        except (urllib.error.URLError, TimeoutError) as error:
            raise ClientError(f"Chat request failed: {type(error).__name__}.") from error

        headers_ms = _elapsed_ms(started_ns)
        first_content_ms: float | None = None
        finish_reason: str | None = None
        usage: dict[str, Any] | None = None
        timings: dict[str, Any] | None = None
        system_fingerprint: str | None = None
        content_parts: list[str] = []
        reasoning_parts: list[str] = []

        try:
            with response:
                for chunk in iter_sse_json(response):
                    fingerprint = chunk.get("system_fingerprint")
                    if fingerprint is not None:
                        system_fingerprint = str(fingerprint)
                    choices = chunk.get("choices")
                    if isinstance(choices, list) and choices:
                        choice = choices[0] if isinstance(choices[0], dict) else {}
                        delta = choice.get("delta") if isinstance(choice.get("delta"), dict) else {}
                        content = delta.get("content")
                        if content not in {None, ""}:
                            if first_content_ms is None:
                                first_content_ms = _elapsed_ms(started_ns)
                            content_parts.append(str(content))
                        reasoning = delta.get("reasoning_content")
                        if reasoning not in {None, ""}:
                            reasoning_parts.append(str(reasoning))
                        if choice.get("finish_reason") is not None:
                            finish_reason = str(choice["finish_reason"])
                    if isinstance(chunk.get("usage"), dict):
                        usage = chunk["usage"]
                    if isinstance(chunk.get("timings"), dict):
                        timings = chunk["timings"]
        except (OSError, TimeoutError) as error:
            raise ClientError(f"Streaming response failed: {type(error).__name__}.") from error

        return StreamResult(
            response_headers_ms=round(headers_ms, 3),
            time_to_first_content_token_ms=(round(first_content_ms, 3) if first_content_ms is not None else None),
            total_latency_ms=round(_elapsed_ms(started_ns), 3),
            finish_reason=finish_reason,
            content="".join(content_parts),
            reasoning_content="".join(reasoning_parts) or None,
            usage=usage,
            timings=timings,
            system_fingerprint=system_fingerprint,
        )


def _elapsed_ms(started_ns: int) -> float:
    return (time.perf_counter_ns() - started_ns) / 1_000_000.0


def _same_path(left: Any, right: str) -> bool:
    if not isinstance(left, str):
        return False
    import os

    return os.path.normcase(os.path.abspath(left)) == os.path.normcase(os.path.abspath(right))
