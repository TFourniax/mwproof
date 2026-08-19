from __future__ import annotations

from datetime import date
import math
from typing import Any, Iterable

from .event_ledger import MilestoneObservation, resolved_forecast_pairs


def _empirical_quantile(values: list[float], q: float) -> float:
    if not values:
        raise ValueError("cannot take quantile of empty values")
    if not 0 < q < 1:
        raise ValueError("quantile must be in (0,1)")
    ordered = sorted(values)
    if len(ordered) == 1:
        return ordered[0]
    pos = (len(ordered) - 1) * q
    lo = math.floor(pos)
    hi = math.ceil(pos)
    if lo == hi:
        return ordered[lo]
    frac = pos - lo
    return ordered[lo] * (1.0 - frac) + ordered[hi] * frac


def _pinball(y: float, pred: float, q: float) -> float:
    err = y - pred
    return q * err if err >= 0 else (1.0 - q) * (-err)


def _actual_evidence_dates(rows: list[MilestoneObservation]) -> dict[tuple[str, str], date]:
    out: dict[tuple[str, str], date] = {}
    for row in rows:
        if row.status != "actual" or not row.actual_date:
            continue
        key = (row.project_id, row.milestone_id)
        observed = date.fromisoformat(row.observed_on)
        if key not in out or observed < out[key]:
            out[key] = observed
    return out


def walk_forward_interval_calibration(
    items: Iterable[MilestoneObservation],
    *,
    milestone_type: str = "operations",
    quantiles: tuple[float, ...] = (0.50, 0.80, 0.90),
    min_history: int = 5,
) -> dict[str, Any]:
    """Evaluate empirical delay quantiles using only then-knowable outcomes.

    Public completion dates are often interval-censored. Coverage is reported as
    bounds: definite coverage requires the entire actual interval below a predicted
    quantile; possible coverage requires any overlap below it.
    """
    if min_history < 2:
        raise ValueError("min_history must be >= 2")
    for q in quantiles:
        if not 0 < q < 1:
            raise ValueError("quantiles must be in (0,1)")

    rows = list(items)
    pairs = [p for p in resolved_forecast_pairs(rows) if p.get("milestone_type") == milestone_type]
    pairs.sort(key=lambda p: (p["forecast_observed_on"], p["project_id"], p["milestone_id"]))
    evidence_dates = _actual_evidence_dates(rows)

    examples: list[dict[str, Any]] = []
    scores: dict[float, dict[str, Any]] = {
        q: {"pinball": [], "definite": 0, "possible": 0, "n": 0} for q in quantiles
    }

    for pair in pairs:
        cutoff = date.fromisoformat(pair["forecast_observed_on"])
        prior = [
            p for p in pairs
            if p is not pair
            and evidence_dates.get((p["project_id"], p["milestone_id"])) is not None
            and evidence_dates[(p["project_id"], p["milestone_id"])] <= cutoff
        ]
        if len(prior) < min_history:
            continue

        history = [float(p["slippage_days"]) for p in prior]
        actual_mid = float(pair["slippage_days"])
        actual_low = float(pair.get("slippage_low_days", actual_mid))
        actual_high = float(pair.get("slippage_high_days", actual_mid))
        predictions: dict[str, float] = {}

        for q in quantiles:
            pred = float(_empirical_quantile(history, q))
            predictions[f"q{int(round(q * 100))}"] = round(pred, 3)
            bucket = scores[q]
            bucket["n"] += 1
            bucket["pinball"].append(_pinball(actual_mid, pred, q))
            if actual_high <= pred:
                bucket["definite"] += 1
            if actual_low <= pred:
                bucket["possible"] += 1

        examples.append({
            "project_id": pair["project_id"],
            "milestone_id": pair["milestone_id"],
            "forecast_observed_on": pair["forecast_observed_on"],
            "history_n": len(prior),
            "actual_slippage_interval_days": {"low": actual_low, "mid": actual_mid, "high": actual_high},
            "predicted_delay_quantiles_days": predictions,
        })

    metrics: dict[str, Any] = {}
    for q in quantiles:
        bucket = scores[q]
        n = bucket["n"]
        pinballs = bucket["pinball"]
        metrics[f"q{int(round(q * 100))}"] = {
            "target_coverage": q,
            "n": n,
            "mean_pinball_loss_days": round(sum(pinballs) / n, 3) if n else None,
            "coverage_lower_bound": round(bucket["definite"] / n, 4) if n else None,
            "coverage_upper_bound": round(bucket["possible"] / n, 4) if n else None,
            "target_inside_coverage_bounds": ((bucket["definite"] / n) <= q <= (bucket["possible"] / n)) if n else None,
        }

    scored = len(examples)
    return {
        "status": "SCORABLE_INTERVAL_CALIBRATION" if scored else "INSUFFICIENT_HISTORY",
        "method": "walk-forward empirical quantiles with interval-censored outcomes and outcome-evidence-time anti-leakage",
        "milestone_type": milestone_type,
        "resolved_examples": len(pairs),
        "scored_examples": scored,
        "min_history": min_history,
        "metrics": metrics,
        "examples": examples,
        "warning": "This is a calibration diagnostic, not a production model. Public data remain non-random and below ProofMW readiness thresholds.",
    }
