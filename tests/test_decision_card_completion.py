from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from proofmw.decision_card import project_decision_card
from proofmw.event_ledger import load_event_ledger

LEDGER = ROOT / "data" / "europe-public-events-v2"


def test_decision_card_separates_documented_and_completed_physical_depth():
    events = load_event_ledger(LEDGER)
    card = project_decision_card(events, "vantage-zrh2", as_of="2026-08-19")
    evidence = card["evidence"]
    assert evidence["physical_coverage_ratio"] > evidence["completed_physical_coverage_ratio"]
    assert {"power", "cooling", "network"}.issubset(set(evidence["physical_types_present"]))
    assert {"power", "cooling", "network"}.issubset(set(evidence["unproven_physical_completion_types"]))
    assert any(x["type"] == "physical_completion_unproven" for x in card["concerns"])
    assert "not proof of physical completion" in card["decision_guardrail"]
