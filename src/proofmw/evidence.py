from __future__ import annotations

from .models import Project


def evidence_coverage(project: Project) -> dict:
    by_id = {e.id: e for e in project.evidence}
    covered = 0
    public = 0
    synthetic = 0
    rows = []
    for gate in project.gates:
        evidence = [by_id[eid] for eid in gate.evidence_ids]
        kinds = sorted({e.kind for e in evidence})
        if evidence:
            covered += 1
        if any(e.kind == "public" for e in evidence):
            public += 1
        if any(e.kind == "synthetic" for e in evidence):
            synthetic += 1
        rows.append({
            "gate_id": gate.id,
            "evidence_count": len(evidence),
            "evidence_kinds": kinds,
            "claims": [e.claim for e in evidence],
        })
    total = len(project.gates)
    return {
        "gate_count": total,
        "covered_gate_ratio": round(covered / total, 4) if total else 1.0,
        "public_evidence_gate_ratio": round(public / total, 4) if total else 1.0,
        "synthetic_assumption_gate_ratio": round(synthetic / total, 4) if total else 0.0,
        "gates": rows,
    }
