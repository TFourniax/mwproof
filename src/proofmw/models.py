from __future__ import annotations

from dataclasses import dataclass, field, asdict
from datetime import date
from typing import Any, Literal

EvidenceKind = Literal["public", "private", "synthetic"]
DistributionKind = Literal["fixed", "triangular", "normal"]


@dataclass(frozen=True)
class Evidence:
    id: str
    title: str
    source_url: str
    kind: EvidenceKind
    observed_on: str
    excerpt: str
    claim: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class Distribution:
    kind: DistributionKind
    low: float
    mode: float
    high: float

    def validate(self) -> None:
        if self.kind == "fixed" and not (self.low == self.mode == self.high):
            raise ValueError("fixed distribution requires low=mode=high")
        if not (self.low <= self.mode <= self.high):
            raise ValueError("distribution must satisfy low <= mode <= high")


@dataclass(frozen=True)
class RiskFactor:
    id: str
    name: str
    delay_days: Distribution
    notes: str = ""

    def validate(self) -> None:
        self.delay_days.validate()


@dataclass(frozen=True)
class CapacityGate:
    id: str
    name: str
    category: str
    max_mw: float
    target_date: str
    delay_days: Distribution
    derate_fraction: Distribution
    depends_on: tuple[str, ...] = ()
    evidence_ids: tuple[str, ...] = ()
    factor_loadings: dict[str, float] = field(default_factory=dict)
    notes: str = ""

    def validate(self) -> None:
        if self.max_mw < 0:
            raise ValueError(f"{self.id}: max_mw must be non-negative")
        date.fromisoformat(self.target_date)
        self.delay_days.validate()
        self.derate_fraction.validate()
        if not (0 <= self.derate_fraction.low <= 1 and 0 <= self.derate_fraction.high <= 1):
            raise ValueError(f"{self.id}: derate_fraction must stay in [0,1]")


@dataclass(frozen=True)
class Project:
    id: str
    name: str
    location: str
    nameplate_mw: float
    currency: str
    gates: tuple[CapacityGate, ...]
    risk_factors: tuple[RiskFactor, ...] = ()
    evidence: tuple[Evidence, ...] = ()
    metadata: dict[str, Any] = field(default_factory=dict)

    def validate(self) -> None:
        if self.nameplate_mw <= 0:
            raise ValueError("nameplate_mw must be positive")
        gate_ids = {g.id for g in self.gates}
        if len(gate_ids) != len(self.gates):
            raise ValueError("gate ids must be unique")
        factor_ids = {f.id for f in self.risk_factors}
        if len(factor_ids) != len(self.risk_factors):
            raise ValueError("risk factor ids must be unique")
        for factor in self.risk_factors:
            factor.validate()
        evidence_ids = {e.id for e in self.evidence}
        if len(evidence_ids) != len(self.evidence):
            raise ValueError("evidence ids must be unique")
        for gate in self.gates:
            gate.validate()
            missing_deps = set(gate.depends_on) - gate_ids
            if missing_deps:
                raise ValueError(f"{gate.id}: missing dependencies {sorted(missing_deps)}")
            missing_factors = set(gate.factor_loadings) - factor_ids
            if missing_factors:
                raise ValueError(f"{gate.id}: missing risk factors {sorted(missing_factors)}")
            missing_evidence = set(gate.evidence_ids) - evidence_ids
            if missing_evidence:
                raise ValueError(f"{gate.id}: missing evidence {sorted(missing_evidence)}")


@dataclass(frozen=True)
class ScenarioOverride:
    gate_id: str
    delay_shift_days: float = 0.0
    max_mw_multiplier: float = 1.0
    derate_additive: float = 0.0


@dataclass(frozen=True)
class UnderwritingRequest:
    as_of_dates: tuple[str, ...]
    quantiles: tuple[float, ...] = (0.50, 0.90, 0.95, 0.99)
    simulations: int = 20000
    seed: int = 42
    overrides: tuple[ScenarioOverride, ...] = ()

    def validate(self) -> None:
        if self.simulations < 100:
            raise ValueError("simulations must be >= 100")
        for value in self.as_of_dates:
            date.fromisoformat(value)
        for q in self.quantiles:
            if not 0 < q < 1:
                raise ValueError("quantiles must be in (0,1)")
