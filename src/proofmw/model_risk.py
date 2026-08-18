from __future__ import annotations

from typing import Any, Iterable

from .calibration import walk_forward_interval_calibration
from .event_ledger import MilestoneObservation
from .readiness import calibration_readiness

DEFAULT_MIN_SCORED = 50
DEFAULT_MAX_COVERAGE_BOUND_WIDTH = 0.15


def model_risk_report(
    items: Iterable[MilestoneObservation],
    *,
    milestone_type: str = "operations",
    min_history: int = 5,
    min_scored: int = DEFAULT_MIN_SCORED,
    max_coverage_bound_width: float = DEFAULT_MAX_COVERAGE_BOUND_WIDTH,
) -> dict[str, Any]:
    """Govern whether empirical confidence outputs are fit to publish.

    This is intentionally conservative. A quantile may only become publishable when
    the corpus passes readiness gates, enough out-of-time examples are scored, and
    empirical coverage is compatible with the claimed confidence level.
    """
    rows = list(items)
    readiness = calibration_readiness(rows)
    calibration = walk_forward_interval_calibration(
        rows, milestone_type=milestone_type, min_history=min_history
    )

    levels: dict[str, Any] = {}
    for label, metric in calibration["metrics"].items():
        reasons: list[str] = []
        n = int(metric["n"] or 0)
        lower = metric["coverage_lower_bound"]
        upper = metric["coverage_upper_bound"]
        if readiness["status"] != "READY_FOR_CALIBRATION":
            reasons.append("dataset_readiness_failed")
        if n < min_scored:
            reasons.append("insufficient_out_of_time_examples")
        if metric["target_inside_coverage_bounds"] is not True:
            reasons.append("claimed_confidence_outside_empirical_coverage_bounds")
        if lower is None or upper is None:
            reasons.append("coverage_not_estimable")
        elif (upper - lower) > max_coverage_bound_width:
            reasons.append("coverage_interval_too_wide")

        levels[label] = {
            "status": "PUBLISHABLE" if not reasons else "DIAGNOSTIC_ONLY",
            "target_coverage": metric["target_coverage"],
            "scored_examples": n,
            "coverage_lower_bound": lower,
            "coverage_upper_bound": upper,
            "mean_pinball_loss_days": metric["mean_pinball_loss_days"],
            "reasons": reasons,
        }

    publishable = [label for label, value in levels.items() if value["status"] == "PUBLISHABLE"]
    return {
        "status": "PUBLISHABLE" if levels and len(publishable) == len(levels) else "NOT_PUBLISHABLE",
        "methodology": "ProofMW Model Risk Policy v0.1",
        "milestone_type": milestone_type,
        "policy": {
            "minimum_scored_out_of_time_examples_per_quantile": min_scored,
            "maximum_interval_censored_coverage_bound_width": max_coverage_bound_width,
            "requires_dataset_readiness": True,
            "requires_claimed_confidence_inside_empirical_coverage_bounds": True,
        },
        "levels": levels,
        "publishable_levels": publishable,
        "blocked_levels": [label for label in levels if label not in publishable],
        "dataset_readiness": readiness,
        "calibration_status": calibration["status"],
        "decision": (
            "Do not present public-data MW@Confidence or COD@Confidence levels as validated probabilities. "
            "They may be shown only as model-development diagnostics until every publication gate passes."
            if len(publishable) != len(levels)
            else "The configured publication gates pass for the evaluated quantiles. Independent model validation and commercial governance are still required."
        ),
    }
