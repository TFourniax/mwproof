from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from proofmw.event_ledger import (
    actual_slippage_days,
    actual_slippage_interval_days,
    detect_source_conflicts,
    ledger_fingerprint,
    ledger_summary,
    load_event_ledger,
    snapshot_as_of,
    target_revision_days,
)
from proofmw.base_rates import delay_base_rate
from proofmw.permitting import permitting_summary
from proofmw.training import build_training_rows, build_hazard_rows

LEDGER = ROOT / "data" / "europe-public-events-v2"


def test_dataset_has_minimum_breadth():
    rows = load_event_ledger(LEDGER)
    summary = ledger_summary(rows)
    assert summary["observations"] >= 137
    assert summary["projects"] >= 64
    assert summary["countries"] >= 12
    assert summary["resolved_forecast_pairs"] >= 22
    assert summary["target_revisions"] >= 14
    assert summary["capacity_revisions"] >= 3


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


def test_coarse_actual_dates_are_intervals_not_fake_exact_days():
    rows = load_event_ledger(LEDGER)
    assert actual_slippage_days(rows, "start-campus-sines", "sin01-operations") == 0
    interval = actual_slippage_interval_days(rows, "start-campus-sines", "sin01-operations")
    assert interval == {"low": -91, "mid": 0, "high": 91}


def test_resolved_operations_use_original_public_forecast():
    rows = load_event_ledger(LEDGER)
    assert actual_slippage_days(rows, "equinix-ml5-phase2", "operations") == 273
    assert actual_slippage_days(rows, "equinix-md2-phase4", "operations") == 182
    assert actual_slippage_days(rows, "equinix-ma5-phase1", "operations") == 91
    assert actual_slippage_days(rows, "equinix-pa10-phase1", "operations") == 122
    assert actual_slippage_days(rows, "equinix-md6-phase1", "operations") == 365
    assert actual_slippage_days(rows, "equinix-madrid-3x1", "operations") == 457


def test_lisbon_lifecycle_has_revision_and_actual():
    rows = load_event_ledger(LEDGER)
    assert actual_slippage_days(rows, "equinix-ls2", "operations") == 108
    revisions = target_revision_days(rows, "equinix-ls2", "operations")
    assert len(revisions) == 1
    assert revisions[0]["revision_days"] == 182


def test_real_atnorth_histories_remain_resolved():
    rows = load_event_ledger(LEDGER)
    assert actual_slippage_days(rows, "atnorth-fin02", "operations") == 243
    assert actual_slippage_days(rows, "atnorth-den01", "operations") == 365


def test_new_primary_operator_histories_are_resolved():
    rows = load_event_ledger(LEDGER)
    for project_id in ["ntt-london1", "ntt-hh4", "ntt-madrid1", "ntt-berlin2", "vantage-zrh1", "vantage-ber2", "vantage-fra2", "vantage-dub1", "digitalrealty-bcn1"]:
        assert actual_slippage_interval_days(rows, project_id, "operations") is not None


def test_public_base_rate_refuses_to_overclaim():
    rows = load_event_ledger(LEDGER)
    rate = delay_base_rate(rows, min_samples=2)
    assert rate["status"] == "descriptive_only"
    assert rate["n"] >= 22
    assert "selection-biased" in rate["warning"]


def test_permitting_summary_tracks_resolved_and_pending():
    rows = load_event_ledger(LEDGER)
    summary = permitting_summary(rows)
    assert summary["projects"] >= 7
    assert summary["positive_resolutions"] >= 3
    assert summary["negative_resolutions"] >= 2
    assert summary["pending"] >= 2


def test_training_exports_are_as_of_safe_and_interval_aware():
    rows = load_event_ledger(LEDGER)
    forecast_rows = build_training_rows(rows)
    hazard_rows = build_hazard_rows(rows)
    assert len(forecast_rows) >= 55
    assert len(hazard_rows) >= 15
    for row in forecast_rows:
        label = row["labels"]
        actual = label["actual_date"]
        if actual:
            # The physical event may predate a later still-public forecast/revision.
            # Anti-leakage is governed by when evidence of the outcome became knowable,
            # not by forcing the retrospective physical date to be after every feature row.
            assert label["actual_window_start"] <= actual <= label["actual_window_end"]
            assert label["actual_evidence_observed_on"] > row["features"]["as_of"]


def test_training_allows_retrospective_physical_date_but_not_future_evidence_leakage():
    rows = load_event_ledger(LEDGER)
    forecast_rows = build_training_rows(rows)
    den_revision = next(
        row for row in forecast_rows
        if row["features"]["project_id"] == "atnorth-den01"
        and row["features"]["as_of"] == "2025-11-26"
    )
    assert den_revision["labels"]["actual_date"] < den_revision["features"]["as_of"]
    assert den_revision["labels"]["actual_evidence_observed_on"] > den_revision["features"]["as_of"]


def test_walk_forward_backtest_does_not_leak_future_outcomes():
    from proofmw.backtest import walk_forward_delay_backtest
    events = load_event_ledger(LEDGER)
    report = walk_forward_delay_backtest(events, milestone_type="operations", min_history=1)
    assert report["status"] == "SCORABLE_BASELINE"
    assert report["resolved_examples"] >= 22
    assert report["historical_baseline_scored_examples"] >= 4
    for row in report["examples"]:
        assert row["prior_resolved_outcomes_available"] < report["resolved_examples"]
        if row["actual_evidence_observed_on"]:
            assert row["actual_evidence_observed_on"] >= row["forecast_observed_on"]


def test_data_quality_objectives_are_now_hard_invariants():
    from proofmw.data_quality import data_quality_report
    events = load_event_ledger(LEDGER)
    report = data_quality_report(events)
    assert report["scope"]["observations"] >= 137
    assert report["scope"]["unique_sources"] >= 70
    assert report["scope"]["operators"] >= 18
    assert report["provenance"]["source_class_counts"]["company-filing"] >= 16
    assert report["provenance"]["authoritative_or_first_party_ratio"] >= 0.50
    assert report["concentration"]["largest_operator_project_share"] <= 0.25
    assert "probability" not in report
    assert "does not convert" in report["interpretation"]


def test_calibration_readiness_improves_but_stays_explicitly_not_ready():
    from proofmw.readiness import calibration_readiness
    events = load_event_ledger(LEDGER)
    report = calibration_readiness(events)
    assert report["status"] == "NOT_READY"
    assert report["gates"]["countries"]["pass"] is True
    assert report["gates"]["operators"]["pass"] is True
    assert report["gates"]["largest_operator_project_share"]["pass"] is True
    assert report["gates"]["authoritative_or_first_party_ratio"]["pass"] is True
    assert report["gates"]["resolved_operations"]["pass"] is False
    assert "resolved_operations" in report["failed_gates"]
    assert "largest_operator_project_share" not in report["failed_gates"]
    assert "authoritative_or_first_party_ratio" not in report["failed_gates"]


def test_ledger_fingerprint_is_order_independent_and_sensitive():
    events = load_event_ledger(LEDGER)
    root = ledger_fingerprint(events)
    assert len(root) == 64
    assert ledger_fingerprint(list(reversed(events))) == root
    assert ledger_fingerprint(events[:-1]) != root
