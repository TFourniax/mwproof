from __future__ import annotations

from collections import defaultdict
from typing import Any, Iterable

from .event_ledger import AUTHORITATIVE_SOURCE_CLASSES, MilestoneObservation

PHYSICAL_TYPES = ("power", "permitting", "transformer", "construction", "cooling", "network")


def physical_depth_report(items: Iterable[MilestoneObservation]) -> dict[str, Any]:
    """Measure evidence depth across physical delivery gates without inferring success."""
    rows = list(items)
    grouped: dict[str, list[MilestoneObservation]] = defaultdict(list)
    for row in rows:
        grouped[row.project_id].append(row)

    projects = []
    for project_id, project_rows in sorted(grouped.items()):
        types = {row.milestone_type for row in project_rows if row.milestone_type in PHYSICAL_TYPES}
        authoritative_types = {
            row.milestone_type
            for row in project_rows
            if row.milestone_type in PHYSICAL_TYPES and row.source_class in AUTHORITATIVE_SOURCE_CLASSES
        }
        projects.append({
            "project_id": project_id,
            "project_name": next((x.project_name for x in project_rows if x.project_name), project_id),
            "operator": next((x.operator for x in project_rows if x.operator), None),
            "country": next((x.country for x in project_rows if x.country), None),
            "physical_types_present": sorted(types),
            "authoritative_physical_types_present": sorted(authoritative_types),
            "physical_type_count": len(types),
            "authoritative_physical_type_count": len(authoritative_types),
            "coverage_ratio": round(len(types) / len(PHYSICAL_TYPES), 4),
            "authoritative_coverage_ratio": round(len(authoritative_types) / len(PHYSICAL_TYPES), 4),
            "missing_types": sorted(set(PHYSICAL_TYPES) - types),
        })

    fully_mapped = [p for p in projects if p["physical_type_count"] == len(PHYSICAL_TYPES)]
    at_least_three = [p for p in projects if p["physical_type_count"] >= 3]
    return {
        "physical_types": list(PHYSICAL_TYPES),
        "projects": len(projects),
        "projects_with_any_physical_evidence": sum(1 for p in projects if p["physical_type_count"] > 0),
        "projects_with_at_least_three_physical_types": len(at_least_three),
        "fully_mapped_projects": len(fully_mapped),
        "fully_mapped_project_ids": [p["project_id"] for p in fully_mapped],
        "project_details": projects,
        "interpretation": "Coverage measures evidence breadth only. Presence of a milestone type does not mean the milestone is complete or successful.",
    }
