from __future__ import annotations

from datetime import date
from typing import Any, Iterable

from .dossier import project_dossier
from .event_ledger import AUTHORITATIVE_SOURCE_CLASSES, MilestoneObservation, actual_window, snapshot_as_of
from .model_risk import model_risk_report
from .physical_depth import PHYSICAL_TYPES


def project_decision_card(
    items: Iterable[MilestoneObservation],
    project_id: str,
    *,
    as_of: str | None = None,
) -> dict[str, Any]:
    """Condense an evidence dossier into an explicit lender diligence card.

    Documentary coverage and physical completion are deliberately separate. A
    design, contract, order or forecast can explain a delivery layer without
    proving that layer has been completed.
    """
    all_rows = list(items)
    rows = snapshot_as_of(all_rows, as_of) if as_of else all_rows
    dossier = project_dossier(rows, project_id, as_of=None)
    project_rows = [x for x in rows if x.project_id == project_id]

    types = {x.milestone_type for x in project_rows if x.milestone_type in PHYSICAL_TYPES}
    authoritative_types = {
        x.milestone_type for x in project_rows
        if x.milestone_type in PHYSICAL_TYPES and x.source_class in AUTHORITATIVE_SOURCE_CLASSES
    }
    completed_types = {
        x.milestone_type for x in project_rows
        if x.milestone_type in PHYSICAL_TYPES and x.status == "actual" and actual_window(x) is not None
    }
    authoritative_completed_types = {
        x.milestone_type for x in project_rows
        if x.milestone_type in PHYSICAL_TYPES
        and x.status == "actual"
        and actual_window(x) is not None
        and x.source_class in AUTHORITATIVE_SOURCE_CLASSES
    }
    missing = sorted(set(PHYSICAL_TYPES) - types)
    unproven_completion = sorted(set(PHYSICAL_TYPES) - completed_types)

    operations = [m for m in dossier["milestones"] if m["milestone_type"] == "operations"]
    operations.sort(
        key=lambda m: (
            (m["latest_forecast"] or {}).get("observed_on") or "",
            (m["actual"] or {}).get("observed_on") or "",
        ),
        reverse=True,
    )
    op_signal = operations[0] if operations else None

    concerns: list[dict[str, Any]] = []
    if missing:
        concerns.append({
            "severity": "HIGH" if len(missing) >= 4 else "MEDIUM",
            "type": "missing_physical_evidence",
            "detail": missing,
        })
    if unproven_completion:
        concerns.append({
            "severity": "HIGH" if len(unproven_completion) >= 4 else "MEDIUM",
            "type": "physical_completion_unproven",
            "detail": unproven_completion,
        })
    if dossier["evidence_summary"]["source_conflicts"]:
        concerns.append({
            "severity": "MEDIUM",
            "type": "source_conflicts",
            "detail": dossier["evidence_summary"]["source_conflicts"],
        })
    stale = dossier["evidence_summary"]["stale_unresolved_forecasts"]
    if stale:
        concerns.append({
            "severity": "MEDIUM",
            "type": "stale_unresolved_forecasts",
            "detail": stale,
        })

    requests = {
        "power": "Executed grid agreement plus energisation/acceptance evidence, live capacity and curtailment terms.",
        "permitting": "Final effective permits, appeal status, conditions precedent and evidence they remain in force.",
        "transformer": "Transformer/switchgear purchase orders, delivery records, FAT/SAT and energisation evidence.",
        "construction": "EPC baseline/current schedule, earned progress, completion certificates and liquidated-damages terms.",
        "cooling": "Cooling procurement, installation, commissioning/acceptance evidence and heat-reuse dependencies.",
        "network": "Carrier contracts, completed diverse fiber routes, tested POEs and meet-me-room readiness.",
    }
    diligence = [requests[t] for t in unproven_completion]
    if not diligence:
        diligence = [
            "Refresh primary evidence for any milestone older than 180 days.",
            "Reconcile public project schedule against lender/EPC data-room dates.",
            "Verify remaining critical-path float and contingency ownership.",
        ]

    risk = model_risk_report(rows, min_history=3)
    mode = "PUBLISHABLE_MODEL" if risk["publishable_levels"] else "EVIDENCE_ONLY"
    today = as_of or max((x.observed_on for x in rows), default=date.today().isoformat())

    return {
        "card_version": "ProofMW Decision Card v1.1",
        "as_of": today,
        "mode": mode,
        "project": dossier["project"],
        "evidence": {
            "observations": dossier["evidence_summary"]["observations"],
            "unique_sources": dossier["evidence_summary"]["unique_sources"],
            "authoritative_or_first_party_observations": dossier["evidence_summary"]["authoritative_or_first_party_observations"],
            "physical_types_present": sorted(types),
            "authoritative_physical_types_present": sorted(authoritative_types),
            "physical_coverage_ratio": round(len(types) / len(PHYSICAL_TYPES), 4),
            "missing_physical_types": missing,
            "completed_physical_types": sorted(completed_types),
            "authoritative_completed_physical_types": sorted(authoritative_completed_types),
            "completed_physical_coverage_ratio": round(len(completed_types) / len(PHYSICAL_TYPES), 4),
            "unproven_physical_completion_types": unproven_completion,
            "source_conflicts": dossier["evidence_summary"]["source_conflicts"],
        },
        "operations_signal": {
            "milestone_id": op_signal["milestone_id"],
            "latest_status": op_signal["latest_status"],
            "latest_forecast": op_signal["latest_forecast"],
            "actual": op_signal["actual"],
            "slippage_interval_days": op_signal["slippage_interval_days"],
        } if op_signal else None,
        "concerns": concerns,
        "next_diligence_requests": diligence,
        "model_risk": {
            "status": risk["status"],
            "publishable_levels": risk["publishable_levels"],
            "blocked_levels": risk["blocked_levels"],
        },
        "decision_guardrail": (
            "No automated approve/decline recommendation is issued. Documentary physical coverage is not proof of physical completion. "
            "This card organizes evidence and missing diligence; quantitative confidence remains blocked unless the independent publication policy passes."
        ),
    }
