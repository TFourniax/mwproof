from __future__ import annotations

from statistics import median
from typing import Any, Iterable

from .event_ledger import MilestoneObservation, resolved_forecast_pairs


def _percentile(values: list[float], p: float) -> float:
    if not values:
        raise ValueError("empty values")
    ordered = sorted(values)
    if len(ordered) == 1:
        return ordered[0]
    pos = (len(ordered) - 1) * p
    lo = int(pos)
    hi = min(len(ordered) - 1, lo + 1)
    frac = pos - lo
    return ordered[lo] * (1 - frac) + ordered[hi] * frac


def delay_base_rate(
    items: Iterable[MilestoneObservation],
    *,
    country: str | None = None,
    milestone_type: str | None = "operations",
    min_samples: int = 2,
) -> dict[str, Any]:
    pairs = resolved_forecast_pairs(items)
    if country:
        pairs = [x for x in pairs if x.get("country") == country]
    if milestone_type:
        pairs = [x for x in pairs if x.get("milestone_type") == milestone_type]
    delays = [float(x["slippage_days"]) for x in pairs]
    if len(delays) < min_samples:
        return {
            "status": "insufficient_data",
            "n": len(delays),
            "country": country,
            "milestone_type": milestone_type,
            "min_samples": min_samples,
            "warning": "Not enough resolved forecast→actual pairs for even a descriptive base rate.",
        }
    p10 = _percentile(delays, 0.10)
    p90 = _percentile(delays, 0.90)
    return {
        "status": "descriptive_only",
        "n": len(delays),
        "country": country,
        "milestone_type": milestone_type,
        "mean_slippage_days": round(sum(delays) / len(delays), 1),
        "median_slippage_days": round(float(median(delays)), 1),
        "p10_slippage_days": round(p10, 1),
        "p90_slippage_days": round(p90, 1),
        "on_or_before_target_ratio": round(sum(1 for x in delays if x <= 0) / len(delays), 4),
        "suggested_triangular_delay_days": {
            "kind": "triangular",
            "low": round(min(delays), 1),
            "mode": round(float(median(delays)), 1),
            "high": round(max(delays), 1),
        },
        "warning": "Public ledger is selection-biased and too small for production underwriting; this output is an empirical seed, not a calibrated probability model.",
    }


def hierarchical_delay_base_rate(
    items: Iterable[MilestoneObservation],
    country: str | None,
    milestone_type: str,
    min_samples: int = 2,
) -> dict[str, Any]:
    """Country/type -> type -> global fallback without pretending sparse slices are calibrated."""
    rows = list(items)
    if country:
        specific = delay_base_rate(rows, country=country, milestone_type=milestone_type, min_samples=min_samples)
        if specific["status"] != "insufficient_data":
            return {"level": "country+milestone_type", **specific}
    typed = delay_base_rate(rows, milestone_type=milestone_type, min_samples=min_samples)
    if typed["status"] != "insufficient_data":
        return {"level": "milestone_type", **typed}
    global_rate = delay_base_rate(rows, milestone_type=None, min_samples=min_samples)
    return {"level": "global", **global_rate}
