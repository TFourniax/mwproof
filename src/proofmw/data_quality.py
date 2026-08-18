from __future__ import annotations

from collections import Counter, defaultdict
from typing import Any, Iterable

from .event_ledger import MilestoneObservation, detect_source_conflicts


def data_quality_report(items: Iterable[MilestoneObservation]) -> dict[str, Any]:
    """Structural data-quality audit. This is not a credit/risk score."""
    rows = list(items)
    by_project: dict[str, list[MilestoneObservation]] = defaultdict(list)
    for row in rows:
        by_project[row.project_id].append(row)

    conflicts = detect_source_conflicts(rows)
    conflicts_by_project = Counter(x["project_id"] for x in conflicts)
    project_rows: list[dict[str, Any]] = []

    for project_id, project_events in sorted(by_project.items()):
        source_urls = {x.source_url for x in project_events}
        source_classes = {x.source_class for x in project_events}
        milestone_ids = {x.milestone_id for x in project_events}
        missing_country = sum(1 for x in project_events if not x.country)
        missing_operator = sum(1 for x in project_events if not x.operator)
        coarse_precision = sum(1 for x in project_events if x.precision in {"year", "half", "half-year", "quarter", "month"})
        project_rows.append({
            "project_id": project_id,
            "project_name": next((x.project_name for x in project_events if x.project_name), None),
            "country": next((x.country for x in project_events if x.country), None),
            "observations": len(project_events),
            "milestones": len(milestone_ids),
            "unique_sources": len(source_urls),
            "source_classes": sorted(source_classes),
            "same_day_conflicts": conflicts_by_project[project_id],
            "missing_country_rows": missing_country,
            "missing_operator_rows": missing_operator,
            "coarse_precision_rows": coarse_precision,
        })

    source_class_counts = Counter(x.source_class for x in rows)
    precision_counts = Counter(x.precision for x in rows)
    unique_sources = {x.source_url for x in rows}
    authoritative = sum(1 for x in rows if x.source_class in {"government", "regulator", "grid-operator", "developer-oem-announcement", "developer-release", "developer", "oem"})

    return {
        "scope": {"observations": len(rows), "projects": len(by_project), "unique_sources": len(unique_sources)},
        "provenance": {
            "source_class_counts": dict(sorted(source_class_counts.items())),
            "authoritative_or_first_party_ratio": round(authoritative / len(rows), 4) if rows else 0.0,
        },
        "precision_counts": dict(sorted(precision_counts.items())),
        "source_conflicts": len(conflicts),
        "projects": project_rows,
        "interpretation": "This report measures structural coverage/provenance only. It deliberately does not convert source classes or completeness into a probability of project success.",
    }
