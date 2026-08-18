from __future__ import annotations

from collections import defaultdict
from datetime import date
from typing import Any, Iterable

from .event_ledger import AUTHORITATIVE_SOURCE_CLASSES, FORECAST_STATUSES, MilestoneObservation, actual_slippage_interval_days, actual_window, capacity_revisions, detect_source_conflicts, target_revision_days


def project_dossier(items: Iterable[MilestoneObservation], project_id: str, *, as_of: str | None = None) -> dict[str, Any]:
    """Build a lender-facing evidence dossier without converting facts to a rating."""
    cutoff = date.fromisoformat(as_of) if as_of else None
    rows = [x for x in items if x.project_id == project_id and (cutoff is None or date.fromisoformat(x.observed_on) <= cutoff)]
    if not rows:
        raise ValueError(f"project not found in ledger: {project_id}")

    rows = sorted(rows, key=lambda x: (x.observed_on, x.milestone_id, -x.source_weight))
    milestone_rows: dict[str, list[MilestoneObservation]] = defaultdict(list)
    for row in rows:
        milestone_rows[row.milestone_id].append(row)

    milestones: list[dict[str, Any]] = []
    all_types: set[str] = set()
    for milestone_id, group in sorted(milestone_rows.items()):
        all_types.update(x.milestone_type for x in group if x.milestone_type)
        forecasts = [x for x in group if x.status in FORECAST_STATUSES and (x.target_start or x.target_end)]
        latest_forecast = sorted(forecasts, key=lambda x: (x.observed_on, x.source_weight))[-1] if forecasts else None
        actuals = [x for x in group if x.status == "actual" and actual_window(x) is not None]
        latest_actual = sorted(actuals, key=lambda x: x.observed_on)[-1] if actuals else None
        latest_bounds = actual_window(latest_actual) if latest_actual else None
        auth = [x for x in group if x.source_class in AUTHORITATIVE_SOURCE_CLASSES]
        milestones.append({
            "milestone_id": milestone_id,
            "milestone_type": next((x.milestone_type for x in group if x.milestone_type), None),
            "latest_status": group[-1].status,
            "latest_forecast": ({"observed_on": latest_forecast.observed_on, "target_start": latest_forecast.target_start, "target_end": latest_forecast.target_end, "capacity_mw": latest_forecast.capacity_mw, "source_url": latest_forecast.source_url, "source_class": latest_forecast.source_class} if latest_forecast else None),
            "actual": ({"observed_on": latest_actual.observed_on, "actual_date": latest_actual.actual_date, "actual_start": latest_bounds[0].isoformat() if latest_bounds else None, "actual_end": latest_bounds[1].isoformat() if latest_bounds else None, "precision": latest_actual.precision, "capacity_mw": latest_actual.capacity_mw, "source_url": latest_actual.source_url, "source_class": latest_actual.source_class} if latest_actual else None),
            "target_revisions": target_revision_days(rows, project_id, milestone_id),
            "capacity_revisions": capacity_revisions(rows, project_id, milestone_id),
            "slippage_interval_days": actual_slippage_interval_days(rows, project_id, milestone_id),
            "source_count": len({x.source_url for x in group}),
            "has_authoritative_or_first_party_evidence": bool(auth),
        })

    conflicts = [x for x in detect_source_conflicts(rows) if x["project_id"] == project_id]
    expected = {"power", "permitting", "construction", "cooling", "network", "operations"}
    missing_physical_types = sorted(expected - all_types)
    stale_forecasts = []
    today = cutoff or date.today()
    for milestone in milestones:
        forecast = milestone["latest_forecast"]
        if forecast:
            age = (today - date.fromisoformat(forecast["observed_on"])).days
            if age > 365 and milestone["actual"] is None:
                stale_forecasts.append({"milestone_id": milestone["milestone_id"], "forecast_age_days": age, "observed_on": forecast["observed_on"]})

    return {
        "project": {"id": project_id, "name": next((x.project_name for x in rows if x.project_name), project_id), "operator": next((x.operator for x in rows if x.operator), None), "country": next((x.country for x in rows if x.country), None), "as_of": as_of},
        "evidence_summary": {"observations": len(rows), "unique_sources": len({x.source_url for x in rows}), "authoritative_or_first_party_observations": sum(1 for x in rows if x.source_class in AUTHORITATIVE_SOURCE_CLASSES), "source_conflicts": len(conflicts), "missing_physical_milestone_types": missing_physical_types, "stale_unresolved_forecasts": stale_forecasts},
        "milestones": milestones,
        "conflicts": conflicts,
        "timeline": [{"observed_on": x.observed_on, "milestone_id": x.milestone_id, "milestone_type": x.milestone_type, "status": x.status, "target_start": x.target_start, "target_end": x.target_end, "actual_date": x.actual_date, "actual_start": x.actual_start, "actual_end": x.actual_end, "capacity_mw": x.capacity_mw, "precision": x.precision, "source_class": x.source_class, "source_weight": x.source_weight, "source_url": x.source_url, "source_title": x.source_title, "notes": x.notes} for x in rows],
        "guardrail": "This dossier is an evidence chronology, not a credit opinion. Missing evidence and stale forecasts remain explicit rather than being imputed as facts. Explicit actual bounds represent interval-censored outcomes rather than fake exact CODs.",
    }
