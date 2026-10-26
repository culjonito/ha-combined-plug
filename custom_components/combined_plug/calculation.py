"""Pure numeric helpers. No Home Assistant dependency; easy to unit-test."""

from __future__ import annotations

from math import isfinite
from collections.abc import Sequence

from .const import CONVERSIONS


def normalize(key: str, value: str | float | int, unit: str | None) -> float | None:
    """Convert a source sensor value into the output unit for *key*."""
    try:
        numeric = float(value)
    except (TypeError, ValueError, OverflowError):
        return None
    if not isfinite(numeric):
        return None
    conversion = CONVERSIONS[key]
    if unit is None:
        # Explicitly assume canonical units if the source omitted its unit.
        # Most compliant Home Assistant measurement sensors declare a unit.
        factor = 100 if key == "power_factor" and 0 <= numeric <= 1 else 1
    else:
        factor = conversion.get(unit)
        if factor is None:
            return None
    return numeric * factor


def combine(key: str, values: Sequence[float], weights: Sequence[float] | None = None) -> float | None:
    """Aggregate N finite values; return None rather than publishing bad data."""
    if len(values) < 2 or not all(isfinite(v) for v in values):
        return None
    if key in ("voltage", "frequency"):
        return sum(values) / len(values)
    if key == "power_factor":
        if weights is not None and len(weights) == len(values) and all(isfinite(w) and w >= 0 for w in weights):
            total_weight = sum(weights)
            if total_weight > 0:
                return sum(value * weight for value, weight in zip(values, weights, strict=True)) / total_weight
        return sum(values) / len(values)
    return sum(values)
