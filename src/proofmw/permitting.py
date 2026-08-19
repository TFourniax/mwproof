from __future__ import annotations

from collections import defaultdict
from datetime import date
from statistics import median
from typing import Any, Iterable

from .event_ledger import MilestoneObservation, TERMINAL_NEGATIVE

POSITIVE_FINAL = {"actual", "final_permission", "approved"}


def permitting_outcomes(items: Iterable[MilestoneObservation]) -> list[dict[str, Any]]:
    grouped: dict[tuple[str, str], list[MilestoneObservation]] = defaultdict(list)
    for item in items:
        if item.milestone_type == "permitting":
            grouped[(item.project_id, item.milestone_id)].append(item)

    outcomes: list[dict[str, Any]] = []
    for (project_id, milestone_id), rows in grouped.items():
        ordered = sorted(rows, key=lambda x: x.observed_on)
        start = ordered[0]
        final = next((x for x in reversed(ordered) if x.status in TERMINAL_NEGATIVE or x.status in POSITIVE_FINAL), None)
        if final is None:
            outcome = "pending"
            duration = None
            resolved_on = None
        else:
            outcome = "negative" if final.status in TERMINAL_NEGATIVE else "positive"
            resolved_on = final.actual_date or final.observed_on
            duration = (date.fromisoformat(resolved_on) - date.fromisoformat(start.observed_on)).days
        outcomes.append({
            "project_id": project_id,
            "project_name": start.project_name,
            "country": start.country,
            "capacity_mw": max((x.capacity_mw or 0.0) for x in ordered) or None,
            "started_on": start.observed_on,
            "resolved_on": resolved_on,
            "duration_days": duration,
            "outcome": outcome,
            "latest_status": ordered[-1].status,
            "events": len(ordered),
        })
    return sorted(outcomes, key=lambda x: (x["country"] or "", x["project_id"]))


def permitting_summary(items: Iterable[MilestoneObservation]) -> dict[str, Any]:
    outcomes = permitting_outcomes(items)
    resolved = [x for x in outcomes if x["outcome"] != "pending"]
    durations = [x["duration_days"] for x in resolved if x["duration_days"] is not None]
    positives = sum(1 for x in resolved if x["outcome"] == "positive")
    negatives = sum(1 for x in resolved if x["outcome"] == "negative")
    return {
        "projects": len(outcomes),
        "resolved": len(resolved),
        "pending": len(outcomes) - len(resolved),
        "positive_resolutions": positives,
        "negative_resolutions": negatives,
        "median_resolution_days": round(float(median(durations)), 1) if durations else None,
        "warning": "Descriptive public-sample statistic only. The ledger is not a random sample and must not be interpreted as an approval probability.",
        "outcomes": outcomes,
    }
