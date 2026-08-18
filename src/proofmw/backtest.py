from __future__ import annotations

from datetime import date
from statistics import median
from typing import Any, Iterable

from .event_ledger import MilestoneObservation, resolved_forecast_pairs


def _mae(errors: list[float]) -> float | None:
    return round(sum(abs(x) for x in errors) / len(errors), 3) if errors else None


def _bias(errors: list[float]) -> float | None:
    return round(sum(errors) / len(errors), 3) if errors else None


def walk_forward_delay_backtest(
    items: Iterable[MilestoneObservation],
    *,
    milestone_type: str = "operations",
    min_history: int = 2,
) -> dict[str, Any]:
    """Backtest public schedule-delay baselines without temporal leakage.

    Each example is predicted using only resolved outcomes whose actual date was
    already observable on or before that example's forecast observation date.
    This intentionally makes early reports sparse rather than leaking future data.
    """
    if min_history < 1:
        raise ValueError("min_history must be >= 1")

    pairs = [p for p in resolved_forecast_pairs(items) if p.get("milestone_type") == milestone_type]
    pairs.sort(key=lambda p: (p["forecast_observed_on"], p["project_id"], p["milestone_id"]))

    examples: list[dict[str, Any]] = []
    developer_errors: list[float] = []
    historical_errors: list[float] = []

    for pair in pairs:
        cutoff = date.fromisoformat(pair["forecast_observed_on"])
        prior = [
            p
            for p in pairs
            if p is not pair
            and date.fromisoformat(p["actual_date"]) <= cutoff
            and p["forecast_observed_on"] < pair["forecast_observed_on"]
        ]
        actual = float(pair["slippage_days"])
        developer_prediction = 0.0
        developer_error = developer_prediction - actual
        developer_errors.append(developer_error)

        historical_prediction: float | None = None
        historical_error: float | None = None
        if len(prior) >= min_history:
            historical_prediction = float(median([float(p["slippage_days"]) for p in prior]))
            historical_error = historical_prediction - actual
            historical_errors.append(historical_error)

        examples.append({
            "project_id": pair["project_id"],
            "milestone_id": pair["milestone_id"],
            "forecast_observed_on": pair["forecast_observed_on"],
            "actual_date": pair["actual_date"],
            "actual_slippage_days": actual,
            "prior_resolved_outcomes_available": len(prior),
            "developer_target_prediction_days": developer_prediction,
            "historical_median_prediction_days": historical_prediction,
            "developer_target_error_days": developer_error,
            "historical_median_error_days": historical_error,
        })

    status = "READY" if historical_errors else "INSUFFICIENT_HISTORY"
    return {
        "status": status,
        "method": "walk-forward; outcomes enter training only after their actual date is knowable",
        "milestone_type": milestone_type,
        "resolved_examples": len(pairs),
        "historical_baseline_scored_examples": len(historical_errors),
        "min_history": min_history,
        "metrics": {
            "developer_target": {"mae_days": _mae(developer_errors), "bias_days": _bias(developer_errors), "n": len(developer_errors)},
            "historical_median": {"mae_days": _mae(historical_errors), "bias_days": _bias(historical_errors), "n": len(historical_errors)},
        },
        "examples": examples,
        "warning": "Public v1 data are selection-biased and sparse. A READY status means the code can score a baseline, not that ProofMW has a production-calibrated underwriting model.",
    }
