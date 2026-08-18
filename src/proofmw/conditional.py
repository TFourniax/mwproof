from __future__ import annotations

from datetime import date
from statistics import median
from typing import Any, Iterable

from .event_ledger import MilestoneObservation, resolved_forecast_pairs


def _mae(errors: list[float]) -> float | None:
    return round(sum(abs(x) for x in errors) / len(errors), 3) if errors else None


def _bias(errors: list[float]) -> float | None:
    return round(sum(errors) / len(errors), 3) if errors else None


def _lead_bucket(days: float | None) -> str:
    if days is None:
        return "unknown"
    if days < 90:
        return "<90d"
    if days < 180:
        return "90-179d"
    if days < 365:
        return "180-364d"
    if days < 730:
        return "1-2y"
    return ">=2y"


def _capacity_bucket(mw: float | None) -> str:
    if mw is None:
        return "unknown"
    if mw < 10:
        return "<10mw"
    if mw < 25:
        return "10-24mw"
    if mw < 50:
        return "25-49mw"
    if mw < 100:
        return "50-99mw"
    return ">=100mw"


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


def _pair_features(pair: dict[str, Any]) -> dict[str, Any]:
    observed = date.fromisoformat(pair["forecast_observed_on"])
    target = date.fromisoformat(pair["forecast_target_midpoint"])
    return {
        "country": pair.get("country"),
        "operator": pair.get("operator"),
        "source_class": pair.get("forecast_source_class"),
        "lead_bucket": _lead_bucket((target - observed).days),
        "capacity_bucket": _capacity_bucket(pair.get("forecast_capacity_mw")),
    }


def conditional_delay_prediction(
    prior: list[dict[str, Any]],
    target: dict[str, Any],
    *,
    min_segment: int = 2,
) -> dict[str, Any]:
    """Interpretable empirical shrinkage baseline.

    The global median is the anchor. Segment medians are allowed to pull the
    estimate only when they have at least ``min_segment`` historical examples.
    This is deliberately dependency-free and conservative: it is a benchmark
    to falsify, not a claim of a trained production model.
    """
    if not prior:
        raise ValueError("at least one prior resolved outcome is required")
    if min_segment < 2:
        raise ValueError("min_segment must be >= 2")

    target_features = _pair_features(target)
    global_values = [float(p["slippage_days"]) for p in prior]
    global_median = float(median(global_values))
    weighted_sum = global_median * 4.0
    total_weight = 4.0
    components = [{
        "feature": "global",
        "value": "all",
        "n": len(global_values),
        "median_slippage_days": round(global_median, 3),
        "weight": 4.0,
    }]

    for feature in ("country", "operator", "source_class", "lead_bucket", "capacity_bucket"):
        value = target_features.get(feature)
        if value in (None, "", "unknown"):
            continue
        matched = [
            float(p["slippage_days"])
            for p in prior
            if _pair_features(p).get(feature) == value
        ]
        if len(matched) < min_segment:
            continue
        seg_median = float(median(matched))
        weight = float(min(len(matched), 6))
        weighted_sum += seg_median * weight
        total_weight += weight
        components.append({
            "feature": feature,
            "value": value,
            "n": len(matched),
            "median_slippage_days": round(seg_median, 3),
            "weight": weight,
        })

    prediction = weighted_sum / total_weight
    return {
        "predicted_slippage_days": round(prediction, 3),
        "global_median_days": round(global_median, 3),
        "features": target_features,
        "components": components,
        "effective_weight": round(total_weight, 3),
        "method": "hierarchical empirical median shrinkage",
    }


def walk_forward_conditional_benchmark(
    items: Iterable[MilestoneObservation],
    *,
    milestone_type: str = "operations",
    min_history: int = 5,
    min_segment: int = 2,
) -> dict[str, Any]:
    """Leakage-safe benchmark of a conditional empirical schedule model.

    Historical outcomes become eligible only after the evidence reporting the
    outcome was public. The benchmark compares three predictions:
      * developer target: 0 days of slippage;
      * global historical median;
      * conditional shrinkage baseline.

    It intentionally does not auto-promote the conditional method into the
    underwriting engine. It must first beat simple baselines out of time.
    """
    if min_history < 2:
        raise ValueError("min_history must be >= 2")
    rows = list(items)
    pairs = [
        dict(p) for p in resolved_forecast_pairs(rows)
        if p.get("milestone_type") == milestone_type
    ]
    forecast_capacities: dict[tuple[str, str, str], float] = {}
    for row in sorted(rows, key=lambda x: x.source_weight):
        if row.capacity_mw is not None and row.status in {"forecast", "revised_forecast", "conflicting_forecast", "delayed"}:
            forecast_capacities[(row.project_id, row.milestone_id, row.observed_on)] = float(row.capacity_mw)
    for pair in pairs:
        pair["forecast_capacity_mw"] = forecast_capacities.get(
            (pair["project_id"], pair["milestone_id"], pair["forecast_observed_on"])
        )
    pairs.sort(key=lambda p: (p["forecast_observed_on"], p["project_id"], p["milestone_id"]))
    evidence_dates = _actual_evidence_dates(rows)

    examples: list[dict[str, Any]] = []
    developer_errors: list[float] = []
    global_errors: list[float] = []
    conditional_errors: list[float] = []

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

        actual = float(pair["slippage_days"])
        global_prediction = float(median([float(p["slippage_days"]) for p in prior]))
        conditional = conditional_delay_prediction(prior, pair, min_segment=min_segment)
        conditional_prediction = float(conditional["predicted_slippage_days"])

        developer_error = -actual
        global_error = global_prediction - actual
        conditional_error = conditional_prediction - actual
        developer_errors.append(developer_error)
        global_errors.append(global_error)
        conditional_errors.append(conditional_error)

        own_outcome_known = evidence_dates.get((pair["project_id"], pair["milestone_id"]))
        examples.append({
            "project_id": pair["project_id"],
            "milestone_id": pair["milestone_id"],
            "country": pair.get("country"),
            "operator": pair.get("operator"),
            "forecast_observed_on": pair["forecast_observed_on"],
            "actual_evidence_observed_on": own_outcome_known.isoformat() if own_outcome_known else None,
            "prior_resolved_outcomes_available": len(prior),
            "actual_slippage_days": actual,
            "predictions_days": {
                "developer_target": 0.0,
                "global_median": round(global_prediction, 3),
                "conditional_empirical": round(conditional_prediction, 3),
            },
            "conditional_components": conditional["components"],
        })

    metrics = {
        "developer_target": {
            "mae_days": _mae(developer_errors),
            "bias_days": _bias(developer_errors),
            "n": len(developer_errors),
        },
        "global_median": {
            "mae_days": _mae(global_errors),
            "bias_days": _bias(global_errors),
            "n": len(global_errors),
        },
        "conditional_empirical": {
            "mae_days": _mae(conditional_errors),
            "bias_days": _bias(conditional_errors),
            "n": len(conditional_errors),
        },
    }
    c_mae = metrics["conditional_empirical"]["mae_days"]
    d_mae = metrics["developer_target"]["mae_days"]
    g_mae = metrics["global_median"]["mae_days"]

    return {
        "status": "SCORABLE_CONDITIONAL_BENCHMARK" if examples else "INSUFFICIENT_HISTORY",
        "method": "walk-forward hierarchical empirical shrinkage; outcome-evidence-time anti-leakage",
        "milestone_type": milestone_type,
        "resolved_examples": len(pairs),
        "scored_examples": len(examples),
        "min_history": min_history,
        "min_segment": min_segment,
        "metrics": metrics,
        "comparison": {
            "conditional_beats_developer_on_mae": (
                c_mae is not None and d_mae is not None and c_mae < d_mae
            ),
            "conditional_beats_global_median_on_mae": (
                c_mae is not None and g_mae is not None and c_mae < g_mae
            ),
        },
        "examples": examples,
        "warning": (
            "This is an interpretable research benchmark, not a production model. "
            "It is deliberately kept outside the underwriting engine until data-readiness, "
            "out-of-time accuracy and calibration gates are earned."
        ),
    }
