from __future__ import annotations

from dataclasses import asdict
from datetime import date, timedelta
import math
import random
from typing import Iterable

from .models import CapacityGate, Distribution, Project, ScenarioOverride, UnderwritingRequest


def _sample(rng: random.Random, d: Distribution) -> float:
    if d.kind == "fixed":
        return d.mode
    if d.kind == "triangular":
        return rng.triangular(d.low, d.high, d.mode)
    if d.kind == "normal":
        sigma = max((d.high - d.low) / 6.0, 1e-9)
        return min(d.high, max(d.low, rng.gauss(d.mode, sigma)))
    raise ValueError(f"unsupported distribution: {d.kind}")


def _sample_factors(project: Project, rng: random.Random) -> dict[str, float]:
    return {factor.id: _sample(rng, factor.delay_days) for factor in project.risk_factors}


def _override_map(overrides: Iterable[ScenarioOverride]) -> dict[str, ScenarioOverride]:
    return {x.gate_id: x for x in overrides}


def _topological_order(project: Project) -> list[CapacityGate]:
    by_id = {g.id: g for g in project.gates}
    visiting: set[str] = set()
    visited: set[str] = set()
    ordered: list[CapacityGate] = []

    def visit(gate_id: str) -> None:
        if gate_id in visited:
            return
        if gate_id in visiting:
            raise ValueError("capacity gate graph contains a cycle")
        visiting.add(gate_id)
        gate = by_id[gate_id]
        for dep in gate.depends_on:
            visit(dep)
        visiting.remove(gate_id)
        visited.add(gate_id)
        ordered.append(gate)

    for gate in project.gates:
        visit(gate.id)
    return ordered


def simulate_once(project: Project, as_of: date, rng: random.Random, overrides: tuple[ScenarioOverride, ...] = ()) -> tuple[float, str]:
    values: dict[str, float] = {}
    critical_gate = "nameplate"
    critical_value = project.nameplate_mw
    override_by_id = _override_map(overrides)
    factor_shocks = _sample_factors(project, rng)

    for gate in _topological_order(project):
        override = override_by_id.get(gate.id)
        shift = override.delay_shift_days if override else 0.0
        multiplier = override.max_mw_multiplier if override else 1.0
        derate_add = override.derate_additive if override else 0.0
        correlated_delay = sum(gate.factor_loadings.get(fid, 0.0) * shock for fid, shock in factor_shocks.items())
        delay = _sample(rng, gate.delay_days) + correlated_delay + shift
        available_on = date.fromisoformat(gate.target_date) + timedelta(days=delay)
        if as_of < available_on:
            value = 0.0
        else:
            derate = min(1.0, max(0.0, _sample(rng, gate.derate_fraction) + derate_add))
            value = max(0.0, gate.max_mw * multiplier * (1.0 - derate))
            if gate.depends_on:
                value = min(value, *(values[d] for d in gate.depends_on))
        values[gate.id] = value
        if value < critical_value:
            critical_value = value
            critical_gate = gate.id

    usable = min(project.nameplate_mw, *(values.values())) if values else project.nameplate_mw
    return usable, critical_gate


def _lower_tail_quantile(samples: list[float], confidence: float) -> float:
    if not samples:
        raise ValueError("no samples")
    sorted_samples = sorted(samples)
    p = 1.0 - confidence
    idx = max(0, min(len(sorted_samples) - 1, math.floor(p * (len(sorted_samples) - 1))))
    return sorted_samples[idx]


def simulate_delivery_date_once(project: Project, rng: random.Random, overrides: tuple[ScenarioOverride, ...] = ()) -> tuple[date, str]:
    dates: dict[str, date] = {}
    override_by_id = _override_map(overrides)
    factor_shocks = _sample_factors(project, rng)
    critical_gate = "nameplate"
    critical_date = date.min
    for gate in _topological_order(project):
        override = override_by_id.get(gate.id)
        shift = override.delay_shift_days if override else 0.0
        correlated_delay = sum(gate.factor_loadings.get(fid, 0.0) * shock for fid, shock in factor_shocks.items())
        own = date.fromisoformat(gate.target_date) + timedelta(days=_sample(rng, gate.delay_days) + correlated_delay + shift)
        effective = max([own] + [dates[d] for d in gate.depends_on])
        dates[gate.id] = effective
        if effective > critical_date:
            critical_date = effective
            critical_gate = gate.id
    return critical_date, critical_gate


def _upper_quantile_dates(samples: list[date], confidence: float) -> date:
    if not samples:
        raise ValueError("no samples")
    ordered = sorted(samples)
    idx = max(0, min(len(ordered) - 1, math.ceil(confidence * len(ordered)) - 1))
    return ordered[idx]


def underwrite(project: Project, request: UnderwritingRequest) -> dict:
    project.validate()
    request.validate()
    rng = random.Random(request.seed)
    results: dict[str, dict] = {}

    schedule_rng = random.Random(request.seed + 1000003)
    delivery_dates: list[date] = []
    delivery_critical: dict[str, int] = {}
    for _ in range(request.simulations):
        delivered_on, critical_gate = simulate_delivery_date_once(project, schedule_rng, request.overrides)
        delivery_dates.append(delivered_on)
        delivery_critical[critical_gate] = delivery_critical.get(critical_gate, 0) + 1
    delivery = {f"COD@{int(round(q * 100))}": _upper_quantile_dates(delivery_dates, q).isoformat() for q in sorted(request.quantiles)}

    for as_of_text in request.as_of_dates:
        as_of = date.fromisoformat(as_of_text)
        capacities: list[float] = []
        critical_counts: dict[str, int] = {}
        for _ in range(request.simulations):
            capacity, critical_gate = simulate_once(project, as_of, rng, request.overrides)
            capacities.append(capacity)
            critical_counts[critical_gate] = critical_counts.get(critical_gate, 0) + 1
        quantile_values = {f"MW@{int(round(q * 100))}": round(_lower_tail_quantile(capacities, q), 3) for q in sorted(request.quantiles)}
        expected = sum(capacities) / len(capacities)
        nonzero = sum(1 for x in capacities if x > 0) / len(capacities)
        full = sum(1 for x in capacities if x >= project.nameplate_mw * 0.999) / len(capacities)
        top_critical = sorted(critical_counts.items(), key=lambda x: (-x[1], x[0]))[:5]
        results[as_of_text] = {
            "capacity": quantile_values,
            "expected_mw": round(expected, 3),
            "probability_any_power": round(nonzero, 6),
            "probability_full_nameplate": round(full, 6),
            "critical_path_frequency": [{"gate_id": gate_id, "frequency": round(count / request.simulations, 6)} for gate_id, count in top_critical],
        }

    return {
        "methodology": "ProofMW Monte Carlo v0.1",
        "project": {"id": project.id, "name": project.name, "nameplate_mw": project.nameplate_mw},
        "request": {"simulations": request.simulations, "seed": request.seed, "quantiles": list(request.quantiles), "overrides": [asdict(x) for x in request.overrides]},
        "delivery_date": delivery,
        "delivery_critical_path_frequency": [{"gate_id": gate_id, "frequency": round(count / request.simulations, 6)} for gate_id, count in sorted(delivery_critical.items(), key=lambda x: (-x[1], x[0]))[:5]],
        "results": results,
    }
