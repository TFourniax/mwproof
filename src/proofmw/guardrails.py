from __future__ import annotations

from .evidence import evidence_coverage
from .models import Project


def underwriting_grade(project: Project) -> dict:
    """Return an evidence-grade, not a credit rating.

    This is intentionally conservative: any synthetic assumptions make a case
    non-verifiable for external credit/insurance use.
    """
    coverage = evidence_coverage(project)
    synthetic = coverage["synthetic_assumption_gate_ratio"]
    public = coverage["public_evidence_gate_ratio"]
    if synthetic > 0:
        grade = "DEMO_ONLY"
        reason = "One or more material capacity gates rely on synthetic assumptions."
    elif public < 1.0:
        grade = "INCOMPLETE"
        reason = "One or more material gates lack source evidence."
    else:
        grade = "EVIDENCE_COMPLETE"
        reason = "All modelled gates have non-synthetic evidence; model calibration still requires independent validation."
    return {"grade": grade, "reason": reason, "coverage": coverage}
