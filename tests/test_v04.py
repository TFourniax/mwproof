from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from proofmw.event_ledger import load_event_ledger
from proofmw.model_risk import model_risk_report
from proofmw.physical_depth import physical_depth_report

LEDGER = ROOT / "data" / "europe-public-events-v2"


def test_model_risk_blocks_unearned_confidence_levels():
    events = load_event_ledger(LEDGER)
    report = model_risk_report(events, min_history=3)
    assert report["status"] == "NOT_PUBLISHABLE"
    assert report["publishable_levels"] == []
    assert "q90" in report["blocked_levels"]
    assert report["levels"]["q90"]["status"] == "DIAGNOSTIC_ONLY"
    assert "dataset_readiness_failed" in report["levels"]["q90"]["reasons"]
    assert "claimed_confidence_outside_empirical_coverage_bounds" in report["levels"]["q90"]["reasons"]


def test_sines_is_first_full_physical_reference_project():
    events = load_event_ledger(LEDGER)
    report = physical_depth_report(events)
    assert "start-campus-sines" in report["fully_mapped_project_ids"]
    sines = next(x for x in report["project_details"] if x["project_id"] == "start-campus-sines")
    assert sines["coverage_ratio"] == 1.0
    assert sines["authoritative_coverage_ratio"] == 1.0
    assert sines["missing_types"] == []


def test_physical_depth_never_claims_completion():
    events = load_event_ledger(LEDGER)
    report = physical_depth_report(events)
    assert "does not mean" in report["interpretation"]
