"""Deterministic graders for inspectable objective quality tasks."""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class GradeResult:
    passed: bool
    reason: str


def grade_response(validator: dict[str, Any], content: str) -> GradeResult:
    candidate = content.strip()
    validator_type = str(validator["type"])
    if validator_type == "exact":
        passed = candidate == str(validator["expected"])
        return GradeResult(passed, "exact_match" if passed else "exact_mismatch")
    if validator_type == "json_exact":
        try:
            actual = json.loads(
                candidate,
                object_pairs_hook=_reject_duplicate_keys,
                parse_constant=_reject_nonstandard_constant,
            )
        except (json.JSONDecodeError, ValueError):
            return GradeResult(False, "invalid_or_duplicate_key_json")
        passed = _json_equal(actual, validator["expected"])
        return GradeResult(passed, "json_match" if passed else "json_mismatch")
    raise ValueError(f"Unsupported quality validator: {validator_type}")


def _reject_duplicate_keys(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"Duplicate JSON key: {key}")
        result[key] = value
    return result


def _reject_nonstandard_constant(value: str) -> None:
    raise ValueError(f"Non-standard JSON constant: {value}")


def _json_equal(actual: Any, expected: Any) -> bool:
    if isinstance(actual, bool) or isinstance(expected, bool):
        return type(actual) is type(expected) and actual == expected
    if isinstance(actual, (int, float)) and isinstance(expected, (int, float)):
        return actual == expected
    if type(actual) is not type(expected):
        return False
    if isinstance(actual, dict):
        return actual.keys() == expected.keys() and all(
            _json_equal(actual[key], expected[key]) for key in actual
        )
    if isinstance(actual, list):
        return len(actual) == len(expected) and all(
            _json_equal(left, right) for left, right in zip(actual, expected)
        )
    return actual == expected
