from pathlib import Path
import sys
import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from proofmw.models import CapacityGate, Distribution, Project


def test_invalid_distribution_rejected():
    d = Distribution("triangular", 2, 1, 3)
    with pytest.raises(ValueError):
        d.validate()


def test_cycle_detected_during_underwriting():
    from proofmw.engine import underwrite
    from proofmw.models import UnderwritingRequest
    d0 = Distribution("fixed", 0, 0, 0)
    g1 = CapacityGate("a", "A", "x", 10, "2026-01-01", d0, d0, ("b",), ())
    g2 = CapacityGate("b", "B", "x", 10, "2026-01-01", d0, d0, ("a",), ())
    p = Project(id="p", name="P", location="X", nameplate_mw=10, currency="EUR", gates=(g1, g2))
    with pytest.raises(ValueError, match="cycle"):
        underwrite(p, UnderwritingRequest(("2026-01-02",), simulations=100))
