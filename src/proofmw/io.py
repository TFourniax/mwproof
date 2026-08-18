from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .models import CapacityGate, Distribution, Evidence, Project, RiskFactor, ScenarioOverride, UnderwritingRequest


def _dist(obj: dict[str, Any]) -> Distribution:
    return Distribution(kind=obj["kind"], low=float(obj["low"]), mode=float(obj["mode"]), high=float(obj["high"]))


def project_from_dict(obj: dict[str, Any]) -> Project:
    evidence = tuple(Evidence(**e) for e in obj.get("evidence", []))
    risk_factors = tuple(RiskFactor(id=f["id"], name=f["name"], delay_days=_dist(f["delay_days"]), notes=f.get("notes", "")) for f in obj.get("risk_factors", []))
    gates = tuple(
        CapacityGate(
            id=g["id"],
            name=g["name"],
            category=g["category"],
            max_mw=float(g["max_mw"]),
            target_date=g["target_date"],
            delay_days=_dist(g["delay_days"]),
            derate_fraction=_dist(g["derate_fraction"]),
            depends_on=tuple(g.get("depends_on", [])),
            evidence_ids=tuple(g.get("evidence_ids", [])),
            factor_loadings={str(k): float(v) for k, v in g.get("factor_loadings", {}).items()},
            notes=g.get("notes", ""),
        )
        for g in obj["gates"]
    )
    project = Project(
        id=obj["id"], name=obj["name"], location=obj["location"],
        nameplate_mw=float(obj["nameplate_mw"]), currency=obj.get("currency", "EUR"),
        gates=gates, risk_factors=risk_factors, evidence=evidence, metadata=obj.get("metadata", {}),
    )
    project.validate()
    return project


def load_project(path: str | Path) -> Project:
    with Path(path).open("r", encoding="utf-8") as f:
        return project_from_dict(json.load(f))


def request_from_dict(obj: dict[str, Any]) -> UnderwritingRequest:
    req = UnderwritingRequest(
        as_of_dates=tuple(obj["as_of_dates"]),
        quantiles=tuple(float(x) for x in obj.get("quantiles", [0.5, 0.9, 0.95, 0.99])),
        simulations=int(obj.get("simulations", 20000)),
        seed=int(obj.get("seed", 42)),
        overrides=tuple(ScenarioOverride(**x) for x in obj.get("overrides", [])),
    )
    req.validate()
    return req
