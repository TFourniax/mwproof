from __future__ import annotations

from collections import defaultdict
from datetime import date
from typing import Any, Iterable

from .event_ledger import MilestoneObservation, FORECAST_STATUSES, TERMINAL_NEGATIVE, _midpoint, actual_window


def build_training_rows(items: Iterable[MilestoneObservation]) -> list[dict[str, Any]]:
    """Build leakage-aware supervised examples from event histories.

    Features contain only information observable at each forecast date. Labels may
    use later outcomes. Actuals are exported as explicit intervals whenever the
    public evidence only bounds the physical completion date.
    """
    grouped: dict[tuple[str, str], list[MilestoneObservation]] = defaultdict(list)
    for item in items:
        grouped[(item.project_id, item.milestone_id)].append(item)

    output: list[dict[str, Any]] = []
    for (project_id, milestone_id), rows in grouped.items():
        ordered = sorted(rows, key=lambda x: (x.observed_on, x.event_id))
        future_actual = next((x for x in reversed(ordered) if x.status == "actual" and actual_window(x) is not None), None)
        future_negative = next((x for x in ordered if x.status in TERMINAL_NEGATIVE), None)
        prior_forecasts = 0
        for observation in ordered:
            if observation.status not in FORECAST_STATUSES or not (observation.target_start or observation.target_end):
                continue
            target = _midpoint(observation.target_start, observation.target_end)
            if target is None:
                continue
            observed = date.fromisoformat(observation.observed_on)
            label_actual = None
            actual_start = None
            actual_end = None
            actual_precision = None
            actual_evidence_observed_on = None
            slippage = None
            slippage_low = None
            slippage_high = None
            if future_actual and date.fromisoformat(future_actual.observed_on) > observed:
                bounds = actual_window(future_actual)
                if bounds is not None:
                    actual_mid = bounds[0] + (bounds[1] - bounds[0]) / 2
                    label_actual = actual_mid.isoformat()
                    actual_start = bounds[0].isoformat()
                    actual_end = bounds[1].isoformat()
                    actual_precision = future_actual.precision
                    actual_evidence_observed_on = future_actual.observed_on
                    slippage = (actual_mid - target).days
                    target_start = date.fromisoformat(observation.target_start or observation.target_end)
                    target_end = date.fromisoformat(observation.target_end or observation.target_start)
                    slippage_low = (bounds[0] - target_end).days
                    slippage_high = (bounds[1] - target_start).days
            canceled = bool(future_negative and date.fromisoformat(future_negative.observed_on) > observed)
            output.append({
                "example_id": f"{project_id}:{milestone_id}:{observation.event_id}",
                "features": {
                    "as_of": observation.observed_on,
                    "project_id": project_id,
                    "country": observation.country,
                    "operator": observation.operator,
                    "milestone_type": observation.milestone_type,
                    "target_midpoint": target.isoformat(),
                    "days_from_observation_to_target": (target - observed).days,
                    "target_window_days": (
                        date.fromisoformat(observation.target_end or observation.target_start)
                        - date.fromisoformat(observation.target_start or observation.target_end)
                    ).days,
                    "capacity_mw": observation.capacity_mw,
                    "source_class": observation.source_class,
                    "source_weight": observation.source_weight,
                    "prior_forecast_revisions": prior_forecasts,
                },
                "labels": {
                    "actual_date": label_actual,
                    "actual_window_start": actual_start,
                    "actual_window_end": actual_end,
                    "actual_precision": actual_precision,
                    "actual_evidence_observed_on": actual_evidence_observed_on,
                    "slippage_days": slippage,
                    "slippage_low_days": slippage_low,
                    "slippage_high_days": slippage_high,
                    "terminal_negative_after_forecast": canceled,
                },
            })
            prior_forecasts += 1
    return output


def build_hazard_rows(items: Iterable[MilestoneObservation]) -> list[dict[str, Any]]:
    """Create as-of rows for permitting/development survival models.

    Resolution availability is based on the date the resolution evidence became
    observable, while physical actual intervals remain separate labels.
    """
    grouped: dict[tuple[str, str], list[MilestoneObservation]] = defaultdict(list)
    for item in items:
        if item.milestone_type in {"permitting", "development"}:
            grouped[(item.project_id, item.milestone_id)].append(item)

    output: list[dict[str, Any]] = []
    for (project_id, milestone_id), rows in grouped.items():
        ordered = sorted(rows, key=lambda x: (x.observed_on, x.event_id))
        for idx, observation in enumerate(ordered):
            future = ordered[idx + 1 :]
            terminal = next((x for x in future if x.status in TERMINAL_NEGATIVE), None)
            positive = next((x for x in future if x.status == "actual" and actual_window(x) is not None), None)
            resolution = terminal or positive
            days_to_resolution = None
            if resolution is not None:
                resolution_date = date.fromisoformat(resolution.observed_on)
                days_to_resolution = (resolution_date - date.fromisoformat(observation.observed_on)).days
            bounds = actual_window(positive) if positive else None
            output.append({
                "example_id": f"hazard:{project_id}:{milestone_id}:{observation.event_id}",
                "features": {
                    "as_of": observation.observed_on,
                    "project_id": project_id,
                    "country": observation.country,
                    "operator": observation.operator,
                    "milestone_type": observation.milestone_type,
                    "status": observation.status,
                    "capacity_mw": observation.capacity_mw,
                    "source_class": observation.source_class,
                    "source_weight": observation.source_weight,
                    "prior_events": idx,
                },
                "labels": {
                    "terminal_negative_after_observation": terminal is not None,
                    "positive_resolution_after_observation": positive is not None and terminal is None,
                    "resolution_evidence_observed_on": resolution.observed_on if resolution else None,
                    "physical_actual_date": positive.actual_date if positive else None,
                    "physical_actual_start": bounds[0].isoformat() if bounds else None,
                    "physical_actual_end": bounds[1].isoformat() if bounds else None,
                    "days_to_resolution": days_to_resolution,
                },
            })
    return output
