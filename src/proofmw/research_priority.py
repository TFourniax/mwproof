from __future__ import annotations

from collections import Counter
import math
from typing import Any, Iterable

from .data_quality import data_quality_report
from .event_ledger import MilestoneObservation, resolved_forecast_pairs
from .readiness import calibration_readiness

_AUTHORITATIVE = {"government", "regulator", "grid-operator", "company-filing", "developer-oem-announcement", "developer-release", "developer", "oem"}


def _needed_for_ratio(numerator: int, denominator: int, target: float) -> int:
    if denominator <= 0:
        return 1
    if numerator / denominator >= target:
        return 0
    return max(0, math.ceil((target * denominator - numerator) / (1.0 - target)))


def research_priorities(items: Iterable[MilestoneObservation]) -> dict[str, Any]:
    """Turn readiness failures into a concrete acquisition queue."""
    rows = list(items)
    readiness = calibration_readiness(rows)
    quality = data_quality_report(rows)
    ops = [p for p in resolved_forecast_pairs(rows) if p.get("milestone_type") == "operations"]

    authoritative = sum(1 for row in rows if row.source_class in _AUTHORITATIVE)
    project_operator: dict[str, str | None] = {}
    for row in rows:
        project_operator.setdefault(row.project_id, row.operator)
    counts = Counter(op for op in project_operator.values() if op)
    leading_operator, leading_count = counts.most_common(1)[0] if counts else (None, 0)
    total_projects = len(project_operator)
    concentration_target = 0.25
    new_non_leader_projects = max(0, math.ceil(leading_count / concentration_target - total_projects)) if leading_count else 0

    controls_early = sum(1 for p in ops if float(p["slippage_days"]) <= 90)
    controls_delayed = sum(1 for p in ops if float(p["slippage_days"]) > 90)

    gaps = {
        "observations": max(0, 500 - len(rows)),
        "projects": max(0, 100 - total_projects),
        "resolved_operations": max(0, 100 - len(ops)),
        "unique_sources": max(0, 100 - quality["scope"]["unique_sources"]),
        "authoritative_events_to_50pct": _needed_for_ratio(authoritative, len(rows), 0.50),
        "non_leading_operator_projects_for_25pct_cap": new_non_leader_projects,
        "early_or_on_time_controls": max(0, 25 - controls_early),
        "materially_delayed_controls": max(0, 25 - controls_delayed),
    }

    recommendations = []
    if gaps["authoritative_events_to_50pct"]:
        recommendations.append({"priority": 1, "objective": "increase_primary_provenance", "target_additions": gaps["authoritative_events_to_50pct"], "preferred_sources": ["regulators", "grid operators", "company filings", "developer releases", "OEM releases"], "why": "Primary evidence improves defensibility and reduces dependence on trade press."})
    if gaps["non_leading_operator_projects_for_25pct_cap"]:
        recommendations.append({"priority": 1, "objective": "deconcentrate_operator_sample", "target_additions": gaps["non_leading_operator_projects_for_25pct_cap"], "avoid_operator": leading_operator, "why": "A concentrated sample can learn operator disclosure behavior instead of infrastructure risk."})
    recommendations.append({"priority": 2, "objective": "resolve_forecast_to_actual_pairs", "target_additions": gaps["resolved_operations"], "preferred_pattern": "historical forecast + dated post-opening confirmation", "why": "Resolved longitudinal pairs are the scarce labels needed for backtesting and calibration."})
    recommendations.append({"priority": 2, "objective": "balance_controls", "target_additions": {"on_time_or_early": gaps["early_or_on_time_controls"], "materially_delayed": gaps["materially_delayed_controls"]}, "why": "A delay-only corpus creates selection bias and unusable base rates."})
    recommendations.append({"priority": 3, "objective": "deepen_physical_milestones", "target_types": ["power", "permitting", "transformer", "construction", "cooling", "commissioning", "network"], "why": "Operations dates alone cannot explain why a project slipped or translate evidence into MW@Confidence."})

    return {
        "readiness_status": readiness["status"],
        "leading_operator": {"name": leading_operator, "projects": leading_count, "share": quality["concentration"]["largest_operator_project_share"]},
        "current": {"observations": len(rows), "projects": total_projects, "resolved_operations": len(ops), "unique_sources": quality["scope"]["unique_sources"], "authoritative_events": authoritative, "authoritative_ratio": quality["provenance"]["authoritative_or_first_party_ratio"], "early_or_on_time_controls": controls_early, "materially_delayed_controls": controls_delayed},
        "gaps": gaps,
        "recommendations": recommendations,
        "failed_readiness_gates": readiness["failed_gates"],
    }
