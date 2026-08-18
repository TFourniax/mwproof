from __future__ import annotations

from datetime import date
from typing import Any, Iterable

from .dossier import project_dossier
from .event_ledger import MilestoneObservation, snapshot_as_of
from .model_risk import model_risk_report
from .physical_depth import PHYSICAL_TYPES


def project_decision_card(
    items: Iterable[MilestoneObservation],
    project_id: str,
    *,
    as_of: str | None = None,
) -> dict[str, Any]:
    """Condense an evidence dossier into an explicit lender diligence card.

    The card never fabricates a numerical credit/risk score. When model-risk
    publication gates are not met, it stays in EVIDENCE_ONLY mode.
    """
    all_rows = list(items)
    rows = snapshot_as_of(all_rows, as_of) if as_of else all_rows
    dossier = project_dossier(rows, project_id, as_of=None)
    project_rows = [x for x in rows if x.project_id == project_id]

    types = {x.milestone_type for x in project_rows if x.milestone_type in PHYSICAL_TYPES}
    authoritative_types = {
        x.milestone_type for x in project_rows
        if x.milestone_type in PHYSICAL_TYPES and x.source_weight >= 0.90
    }
    missing = sorted(set(PHYSICAL_TYPES) - types)

    operations = [
        m for m in dossier["milestones"]
        if m["milestone_type"] == "operations"
    ]
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

    diligence: list[str] = []
    requests = {
        "power": "Executed grid-connection agreement, energisation schedule and curtailment terms.",
        "permitting": "Final permits, appeal status and remaining planning conditions.",
        "transformer": "Transformer/switchgear purchase orders, OEM slots and FAT/SAT dates.",
        "construction": "EPC schedule, critical path, earned progress and liquidated-damages terms.",
        "cooling": "Cooling design, procurement status, commissioning and heat-reuse dependencies.",
        "network": "Diverse carrier routes, fiber completion and meet-me-room readiness.",
    }
    for missing_type in missing:
        diligence.append(requests[missing_type])
    if not diligence:
        diligence = [
            "Refresh primary evidence for any milestone older than 180 days.",
            "Reconcile project schedule against lender/EPC data-room dates.",
            "Verify remaining critical-path float and contingency ownership.",
        ]

    risk = model_risk_report(rows, min_history=3)
    mode = "PUBLISHABLE_MODEL" if risk["publishable_levels"] else "EVIDENCE_ONLY"
    today = as_of or max((x.observed_on for x in rows), default=date.today().isoformat())

    return {
        "card_version": "ProofMW Decision Card v1",
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
            "No automated approve/decline recommendation is issued. "
            "This card organizes evidence and missing diligence. Quantitative confidence "
            "levels remain blocked unless the independent publication policy passes."
        ),
    }
