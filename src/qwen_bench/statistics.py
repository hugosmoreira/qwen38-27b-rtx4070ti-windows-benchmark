"""Small, explicit statistical helpers used in public result records."""

from __future__ import annotations

import math
from collections.abc import Iterable


def descriptive_statistics(values: Iterable[float | int | None]) -> dict[str, float | int | None] | None:
    """Return rounded mean, sample SD, CV, minimum, and maximum.

    Missing values are excluded. A single observation has a sample standard
    deviation of zero. CV is undefined when the mean is zero and is stored as
    ``None`` rather than an invented zero.
    """

    numbers = [float(value) for value in values if value is not None]
    if not numbers:
        return None

    count = len(numbers)
    mean = sum(numbers) / count
    if count == 1:
        sample_standard_deviation = 0.0
    else:
        squared_error = sum((value - mean) ** 2 for value in numbers)
        sample_standard_deviation = math.sqrt(squared_error / (count - 1))

    return {
        "count": count,
        "mean": round(mean, 3),
        "sample_standard_deviation": round(sample_standard_deviation, 3),
        "coefficient_of_variation_percent": (
            round((sample_standard_deviation / mean) * 100.0, 3) if mean != 0 else None
        ),
        "minimum": round(min(numbers), 3),
        "maximum": round(max(numbers), 3),
    }
