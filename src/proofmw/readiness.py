from __future__ import annotations

from typing import Any, Iterable

from .data_quality import data_quality_report
from .event_ledger import MilestoneObservation, resolved_forecast_pairs


def calibration_readiness(items: Iterable[MilestoneObservation]) -> dict[str, Any]:
    """Hard gates for claiming a production-calibrated public-data model.

    No blended score: failing any critical gate keeps the dataset NOT_READY.
    Thresholds are deliberately demanding and can be versioned with methodology.
    """
    rows = list(items)
    quality = data_quality_report(rows)
    ops = [p for p in resolved_forecast_pairs(rows) if p.get("milestone_type") == "operations"]
    early_or_on_time = sum(1 for p in ops if p["slippage_days"] <= 90)
    materially_delayed = sum(1 for p in ops if p["slippage_days"] > 90)
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
        "note": "These are minimum data-volume/diversity gates only. Passing them does not prove predictive performance; leakage-free backtests and calibration tests remain mandatory.",
    }
