from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from proofmw.event_ledger import load_event_ledger, ledger_summary, detect_source_conflicts, snapshot_as_of, actual_slippage_days
from proofmw.base_rates import delay_base_rate
from proofmw.permitting import permitting_summary
from proofmw.training import build_training_rows, build_hazard_rows

LEDGER = ROOT / "data" / "europe-public-events-v1.json"


def test_dataset_has_minimum_breadth():
    rows = load_event_ledger(LEDGER)
    summary = ledger_summary(rows)
    assert summary["observations"] >= 35
    assert summary["projects"] >= 14
    assert summary["countries"] >= 7
    assert summary["resolved_forecast_pairs"] >= 3


def test_known_fin04_conflict_is_preserved():
    rows = load_event_ledger(LEDGER)
    conflicts = detect_source_conflicts(rows)
    fin04 = [x for x in conflicts if x["project_id"] == "atnorth-fin04"]
    assert len(fin04) == 1
    assert fin04[0]["target_spread_days"] >= 300


def test_snapshot_prevents_lookahead():
    rows = load_event_ledger(LEDGER)
    snap = snapshot_as_of(rows, "2024-12-31")
    assert all(x.observed_on <= "2024-12-31" for x in snap)
    assert not any(x.project_id == "stack-babenhausen" for x in snap)


def test_resolved_operations_have_observed_slippage():
    rows = load_event_ledger(LEDGER)
    assert actual_slippage_days(rows, "start-campus-sines", "sin01-operations") == 46
    assert actual_slippage_days(rows, "atnorth-fin02", "operations") == 258
    assert actual_slippage_days(rows, "atnorth-den01", "operations") == 411


def test_public_base_rate_refuses_to_overclaim():
    rows = load_event_ledger(LEDGER)
    rate = delay_base_rate(rows, min_samples=2)
    assert rate["status"] == "descriptive_only"
    assert rate["n"] >= 3
    assert "warning" in rate


def test_permitting_summary_tracks_resolved_and_pending():
    rows = load_event_ledger(LEDGER)
    summary = permitting_summary(rows)
    assert summary["projects"] >= 7
    assert summary["positive_resolutions"] >= 3
    assert summary["negative_resolutions"] >= 2
    assert summary["pending"] >= 2


def test_training_exports_are_as_of_safe():
    rows = load_event_ledger(LEDGER)
    forecast_rows = build_training_rows(rows)
    hazard_rows = build_hazard_rows(rows)
    assert len(forecast_rows) >= 10
    assert len(hazard_rows) >= 15
    for row in forecast_rows:
        actual = row["labels"]["actual_date"]
        if actual:
            assert actual >= row["features"]["as_of"]


def test_walk_forward_backtest_refuses_future_leakage():
    from proofmw.backtest import walk_forward_delay_backtest
    events = load_event_ledger(LEDGER)
    report = walk_forward_delay_backtest(events, milestone_type="operations", min_history=1)
    assert report["resolved_examples"] >= 3
    for row in report["examples"]:
        assert row["prior_resolved_outcomes_available"] < report["resolved_examples"]


def test_data_quality_report_is_structural_not_credit_scoring():
    from proofmw.data_quality import data_quality_report
    events = load_event_ledger(LEDGER)
    report = data_quality_report(events)
    assert report["scope"]["observations"] >= 35
    assert report["scope"]["unique_sources"] >= 20
    assert "probability" not in report
    assert "does not convert" in report["interpretation"]
