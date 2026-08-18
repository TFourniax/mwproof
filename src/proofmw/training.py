from __future__ import annotations

from collections import defaultdict
from datetime import date
from typing import Any, Iterable

from .event_ledger import MilestoneObservation, FORECAST_STATUSES, TERMINAL_NEGATIVE, _midpoint, actual_window


def build_training_rows(items: Iterable[MilestoneObservation]) -> list[dict[str, Any]]:
    """Build leakage-aware supervised examples from event histories.

    Features contain only information observable at each forecast date. Labels may
    use later outcomes. This file is an export primitive, not an ML model.
    """
    grouped: dict[tuple[str, str], list[MilestoneObservation]] = defaultdict(list)
    for item in items:
        grouped[(item.project_id, item.milestone_id)].append(item)

    output: list[dict[str, Any]] = []
    for (project_id, milestone_id), rows in grouped.items():
        ordered = sorted(rows, key=lambda x: (x.observed_on, x.event_id))
        future_actual = next((x for x in reversed(ordered) if x.status == "actual" and x.actual_date), None)
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
            slippage = None
            if future_actual and future_actual.actual_date and date.fromisoformat(future_actual.observed_on) > observed:
                bounds = actual_window(future_actual)
                if bounds is not None:
                    actual_mid = bounds[0] + (bounds[1] - bounds[0]) / 2
                    label_actual = future_actual.actual_date
                    slippage = (actual_mid - target).days
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
                    "target_window_days": (date.fromisoformat(observation.target_end or observation.target_start) - date.fromisoformat(observation.target_start or observation.target_end)).days,
                    "capacity_mw": observation.capacity_mw,
                    "source_class": observation.source_class,
                    "source_weight": observation.source_weight,
                    "prior_forecast_revisions": prior_forecasts,
                },
                "labels": {
                    "actual_date": label_actual,
                    "slippage_days": slippage,
                    "terminal_negative_after_forecast": canceled,
                },
            })
            prior_forecasts += 1
    return output


def build_hazard_rows(items: Iterable[MilestoneObservation]) -> list[dict[str, Any]]:
    """Create as-of rows for permitting/development survival models."""
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
            positive = next((x for x in future if x.status == "actual" and x.actual_date), None)
            resolution = terminal or positive
            days_to_resolution = None
            if resolution is not None:
                resolution_date = date.fromisoformat(resolution.actual_date or resolution.observed_on)
                days_to_resolution = (resolution_date - date.fromisoformat(observation.observed_on)).days
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
                    "days_to_resolution": days_to_resolution,
                },
            })
    return output
