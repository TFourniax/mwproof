from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from proofmw.event_ledger import load_event_ledger, target_revision_days, actual_slippage_days

LEDGER = ROOT / "data" / "europe-public-events-v0.json"


def test_public_event_ledger_detects_target_revision():
    events = load_event_ledger(LEDGER)
    revisions = target_revision_days(events, "start-campus-sines", "sin02-ready-for-service")
    assert len(revisions) == 1
    assert revisions[0]["revision_days"] > 365


def test_actual_slippage_can_be_derived_when_actual_exists():
    events = load_event_ledger(LEDGER)
    slippage = actual_slippage_days(events, "start-campus-sines", "sin01-operations")
    assert slippage is not None
    assert slippage >= 0
