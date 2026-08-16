"""Paired calculations for two objective quality-evaluation records."""

from __future__ import annotations

import math
from typing import Any


def compare_quality_results(q2: dict[str, Any], iq2: dict[str, Any]) -> dict[str, Any]:
    q2_tasks = q2.get("tasks")
    iq2_tasks = iq2.get("tasks")
    if not isinstance(q2_tasks, list) or not isinstance(iq2_tasks, list):
        raise ValueError("Both quality records must contain task arrays.")
    q2_ids = [task.get("task_id") for task in q2_tasks if isinstance(task, dict)]
    iq2_ids = [task.get("task_id") for task in iq2_tasks if isinstance(task, dict)]
    if q2_ids != iq2_ids or len(q2_ids) != len(q2_tasks) or len(iq2_ids) != len(iq2_tasks):
        raise ValueError("Quality records must contain the same tasks in the same order.")
    if not q2_ids:
        raise ValueError("Quality records must contain at least one paired task.")
    if q2.get("prompt_suite") != iq2.get("prompt_suite"):
        raise ValueError("Quality records must reference the same prompt suite.")

    both_pass = q2_only = iq2_only = neither_pass = 0
    task_outcomes: list[dict[str, Any]] = []
    for q2_task, iq2_task in zip(q2_tasks, iq2_tasks):
        if q2_task.get("category") != iq2_task.get("category"):
            raise ValueError("Paired quality tasks must have matching categories.")
        if q2_task.get("validator_type") != iq2_task.get("validator_type"):
            raise ValueError("Paired quality tasks must use matching validator types.")
        q2_passed = q2_task.get("passed") is True
        iq2_passed = iq2_task.get("passed") is True
        if q2_passed and iq2_passed:
            outcome = "both_pass"
            both_pass += 1
        elif q2_passed:
            outcome = "q2_only"
            q2_only += 1
        elif iq2_passed:
            outcome = "iq2_only"
            iq2_only += 1
        else:
            outcome = "neither_pass"
            neither_pass += 1
        task_outcomes.append(
            {
                "task_id": q2_task["task_id"],
                "category": q2_task["category"],
                "q2_passed": q2_passed,
                "iq2_passed": iq2_passed,
                "paired_outcome": outcome,
            }
        )

    total = len(q2_ids)
    q2_passes = both_pass + q2_only
    iq2_passes = both_pass + iq2_only
    return {
        "tasks": total,
        "q2_passes": q2_passes,
        "iq2_passes": iq2_passes,
        "q2_pass_rate_percent": round((q2_passes / total) * 100, 3),
        "iq2_pass_rate_percent": round((iq2_passes / total) * 100, 3),
        "q2_minus_iq2_passes": q2_passes - iq2_passes,
        "q2_minus_iq2_percentage_points": round(((q2_passes - iq2_passes) / total) * 100, 3),
        "paired_contingency": {
            "both_pass": both_pass,
            "q2_only": q2_only,
            "iq2_only": iq2_only,
            "neither_pass": neither_pass,
        },
        "discordant_tasks": q2_only + iq2_only,
        "two_sided_exact_mcnemar_p": exact_mcnemar_two_sided(q2_only, iq2_only),
        "task_outcomes": task_outcomes,
    }


def exact_mcnemar_two_sided(left_only: int, right_only: int) -> float:
    if left_only < 0 or right_only < 0:
        raise ValueError("Discordant counts cannot be negative.")
    discordant = left_only + right_only
    if discordant == 0:
        return 1.0
    tail = sum(math.comb(discordant, value) for value in range(min(left_only, right_only) + 1))
    probability = min(1.0, 2.0 * tail / (2**discordant))
    return round(probability, 6)
