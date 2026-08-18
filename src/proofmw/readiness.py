from __future__ import annotations

from typing import Any, Iterable

from .data_quality import data_quality_report
from .event_ledger import MilestoneObservation, resolved_forecast_pairs


def calibration_readiness(items: Iterable[MilestoneObservation]) -> dict[str, Any]:
    """Hard gates for claiming a production-calibrated public-data model.

    No blended score: failing any critical gate keeps the dataset NOT_READY.
    Coarse or bounded outcomes are classified conservatively: a case is an
    on-time control only if its whole slippage interval is <=90 days, and a
    delayed control only if its whole interval is >90 days. Cases crossing the
    threshold remain ambiguous instead of being forced into a class by midpoint.
    """
    rows = list(items)
    quality = data_quality_report(rows)
    ops = [p for p in resolved_forecast_pairs(rows) if p.get("milestone_type") == "operations"]
    early_or_on_time = sum(1 for p in ops if p["slippage_high_days"] <= 90)
    materially_delayed = sum(1 for p in ops if p["slippage_low_days"] > 90)
    ambiguous_controls = len(ops) - early_or_on_time - materially_delayed
    thresholds = {
        "observations": (len(rows), 500),
        "projects": (quality["scope"]["projects"], 100),
        "resolved_operations": (len(ops), 100),
        "countries": (len({x.country for x in rows if x.country}), 5),
        "operators": (quality["scope"]["operators"], 10),
        "unique_sources": (quality["scope"]["unique_sources"], 100),
        "authoritative_or_first_party_ratio": (quality["provenance"]["authoritative_or_first_party_ratio"], 0.50),
        "early_or_on_time_controls": (early_or_on_time, 25),
        "materially_delayed_controls": (materially_delayed, 25),
    }
    gates = {
        name: {"actual": actual, "required": required, "operator": ">=", "pass": actual >= required}
        for name, (actual, required) in thresholds.items()
    }
    concentration = quality["concentration"]["largest_operator_project_share"]
    gates["largest_operator_project_share"] = {"actual": concentration, "required": 0.25, "operator": "<=", "pass": concentration <= 0.25}
    failed = [name for name, gate in gates.items() if not gate["pass"]]
    return {
        "status": "READY_FOR_CALIBRATION" if not failed else "NOT_READY",
        "gates": gates,
        "failed_gates": failed,
        "control_labels": {
            "certainly_early_or_on_time": early_or_on_time,
            "certainly_materially_delayed": materially_delayed,
            "interval_ambiguous": ambiguous_controls,
        },
        "note": "These are minimum data-volume/diversity gates only. Interval-censored cases crossing the 90-day control threshold are excluded from both classes. Passing all gates still does not prove predictive performance.",
    }
