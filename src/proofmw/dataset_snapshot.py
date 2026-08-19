from __future__ import annotations

from collections import Counter, defaultdict
from datetime import date
from typing import Any, Iterable

from .data_quality import data_quality_report
from .event_ledger import AUTHORITATIVE_SOURCE_CLASSES, FORECAST_STATUSES, MilestoneObservation, actual_window, ledger_fingerprint, resolved_forecast_pairs, snapshot_as_of
from .physical_depth import physical_depth_report
from .readiness import calibration_readiness


def dataset_snapshot(items: Iterable[MilestoneObservation], *, as_of: str | None = None) -> dict[str, Any]:
    """Build a reproducible, dated statement of corpus coverage."""
    all_rows = list(items)
    if not all_rows:
        raise ValueError("cannot snapshot an empty ledger")
    cutoff = as_of or max(x.observed_on for x in all_rows)
    date.fromisoformat(cutoff)
    rows = snapshot_as_of(all_rows, cutoff)
    if not rows:
        raise ValueError("no observations are knowable at the requested as_of date")

    quality = data_quality_report(rows)
    readiness = calibration_readiness(rows)
    physical = physical_depth_report(rows)
    resolved = resolved_forecast_pairs(rows)
    resolved_ops = [p for p in resolved if p.get("milestone_type") == "operations"]
    observation_dates = [date.fromisoformat(x.observed_on) for x in rows]
    actual_bounds = [actual_window(x) for x in rows if x.status == "actual" and actual_window(x) is not None]
    physical_midpoints = [a + (b - a) / 2 for a, b in actual_bounds]
    by_year = Counter(d.year for d in observation_dates)
    actual_by_year = Counter(d.year for d in physical_midpoints)

    grouped: dict[tuple[str, str], list[MilestoneObservation]] = defaultdict(list)
    for row in rows:
        grouped[(row.project_id, row.milestone_id)].append(row)

    unresolved: list[dict[str, Any]] = []
    today = date.fromisoformat(cutoff)
    for (project_id, milestone_id), group in sorted(grouped.items()):
        forecasts = [x for x in group if x.status in FORECAST_STATUSES and (x.target_start or x.target_end)]
        has_confirmed_actual = any(x.status == "actual" for x in group)
        has_negative = any(x.status in {"canceled", "denied", "withdrawn"} for x in group)
        if not forecasts or has_confirmed_actual or has_negative:
            continue
        latest = max(forecasts, key=lambda x: (x.observed_on, x.source_weight))
        target_end = latest.target_end or latest.target_start
        overdue_days = max(0, (today - date.fromisoformat(target_end)).days) if target_end else None
        unresolved.append({"project_id": project_id, "project_name": latest.project_name, "operator": latest.operator, "country": latest.country, "milestone_id": milestone_id, "milestone_type": latest.milestone_type, "forecast_observed_on": latest.observed_on, "target_start": latest.target_start, "target_end": latest.target_end, "overdue_days": overdue_days, "source_url": latest.source_url})
    overdue = [x for x in unresolved if (x["overdue_days"] or 0) > 0]
    stale = [x for x in unresolved if (today - date.fromisoformat(x["forecast_observed_on"])).days > 365]

    source_domains = {x.source_url.split("/", 3)[2].lower().removeprefix("www.") for x in rows}
    certain_on_time = sum(1 for p in resolved_ops if p["slippage_high_days"] <= 90)
    certain_delayed = sum(1 for p in resolved_ops if p["slippage_low_days"] > 90)
    ambiguous = len(resolved_ops) - certain_on_time - certain_delayed
    unscored_actual = sum(1 for x in rows if x.status == "actual" and actual_window(x) is None)

    return {
        "snapshot_version": "ProofMW Coverage Snapshot v1.2",
        "as_of": cutoff,
        "ledger_sha256": ledger_fingerprint(rows),
        "coverage_claim": "Dated public-evidence coverage snapshot; not a claim of complete market coverage or universal market completeness. Absence from the ledger means not yet evidenced in this corpus, not absence in reality.",
        "scope": {"observations": len(rows), "projects": quality["scope"]["projects"], "operators": quality["scope"]["operators"], "countries": len({x.country for x in rows if x.country}), "unique_sources": quality["scope"]["unique_sources"], "unique_source_domains": len(source_domains), "milestones": len(grouped), "resolved_forecast_pairs": len(resolved), "resolved_operations": len(resolved_ops)},
        "temporal_coverage": {"first_evidence_observed_on": min(observation_dates).isoformat(), "latest_evidence_observed_on": max(observation_dates).isoformat(), "first_physical_actual_bound": min(a for a, _ in actual_bounds).isoformat() if actual_bounds else None, "latest_physical_actual_bound": max(b for _, b in actual_bounds).isoformat() if actual_bounds else None, "observations_by_year": dict(sorted(by_year.items())), "physical_actual_midpoints_by_year": dict(sorted(actual_by_year.items()))},
        "provenance": {**quality["provenance"], "authoritative_observations": sum(1 for x in rows if x.source_class in AUTHORITATIVE_SOURCE_CLASSES)},
        "temporal_precision": quality["temporal_precision"],
        "concentration": quality["concentration"],
        "labels": {"resolved_operations": len(resolved_ops), "certainly_early_or_on_time_operations": certain_on_time, "certainly_materially_delayed_operations": certain_delayed, "interval_ambiguous_operations": ambiguous, "confirmed_actual_without_scorable_time": unscored_actual, "terminal_negative_events": sum(1 for x in rows if x.status in {"canceled", "denied", "withdrawn"}), "classification_rule": "Control labels require the whole slippage interval to fall on one side of the 90-day threshold; current-state confirmations without a defensible date are not scored."},
        "open_forecasts": {"unresolved": len(unresolved), "overdue": len(overdue), "stale_over_365d": len(stale), "top_overdue": sorted(overdue, key=lambda x: x["overdue_days"] or 0, reverse=True)[:25]},
        "physical_depth": {
            "projects_with_any_physical_evidence": physical["projects_with_any_physical_evidence"],
            "projects_with_at_least_three_physical_types": physical["projects_with_at_least_three_physical_types"],
            "fully_mapped_projects": physical["fully_mapped_projects"],
            "fully_mapped_project_ids": physical["fully_mapped_project_ids"],
            "projects_with_any_completed_physical_type": physical["projects_with_any_completed_physical_type"],
            "projects_with_at_least_three_completed_physical_types": physical["projects_with_at_least_three_completed_physical_types"],
            "fully_completed_physical_projects": physical["fully_completed_physical_projects"],
            "fully_completed_physical_project_ids": physical["fully_completed_physical_project_ids"],
            "interpretation": "Documentary physical coverage is not physical completion. Completion requires an actual event with a defensible physical time window."
        },
        "readiness": {"status": readiness["status"], "failed_gates": readiness["failed_gates"], "gates": readiness["gates"], "control_labels": readiness["control_labels"]},
    }
