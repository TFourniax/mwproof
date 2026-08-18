from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from proofmw.dataset_snapshot import dataset_snapshot
from proofmw.event_ledger import actual_slippage_interval_days, load_event_ledger, timeline
from proofmw.physical_depth import physical_depth_report

LEDGER = ROOT / "data" / "europe-public-events-v2"


def test_deepening_layer_materially_expands_corpus():
    events = load_event_ledger(LEDGER)
    snap = dataset_snapshot(events, as_of="2026-08-19")
    assert snap["scope"]["observations"] >= 238
    assert snap["scope"]["unique_sources"] >= 135
    assert snap["scope"]["resolved_operations"] >= 33


def test_md5_is_now_a_real_scorable_resolved_operation():
    events = load_event_ledger(LEDGER)
    interval = actual_slippage_interval_days(events, "equinix-md5-phase1", "operations")
    assert interval is not None
    md5 = timeline(events, "equinix-md5-phase1", "operations")
    actual = [x for x in md5 if x.status == "actual"][-1]
    assert actual.actual_date == "2026-05-22"
    assert actual.source_class == "developer-release"


def test_fra5_current_operation_is_confirmed_but_not_fake_dated():
    events = load_event_ledger(LEDGER)
    fra5 = timeline(events, "cyrusone-fra5", "operations")
    confirmed = [x for x in fra5 if x.status == "actual"][-1]
    assert confirmed.observed_on == "2026-08-19"
    assert confirmed.actual_date is None
    assert confirmed.actual_start is None
    snap = dataset_snapshot(events, as_of="2026-08-19")
    assert not any(
        x["project_id"] == "cyrusone-fra5" and x["milestone_id"] == "operations"
        for x in snap["open_forecasts"]["top_overdue"]
    )


def test_fra7_append_only_correction_preserves_old_row_but_latest_truth_is_2024():
    events = load_event_ledger(LEDGER)
    rows = timeline(events, "cyrusone-fra7", "construction_start")
    actuals = [x for x in rows if x.status == "actual"]
    assert len(actuals) >= 2
    assert any(x.actual_date == "2025-01-29" for x in actuals)
    corrected = actuals[-1]
    assert corrected.observed_on == "2026-08-19"
    assert corrected.actual_date == "2024-07-19"
    assert "correction" in corrected.notes.lower()


def test_design_depth_does_not_masquerade_as_completed_physical_delivery():
    events = load_event_ledger(LEDGER)
    report = physical_depth_report(events)
    zrh2 = next(x for x in report["project_details"] if x["project_id"] == "vantage-zrh2")
    assert {"power", "cooling", "network"}.issubset(set(zrh2["physical_types_present"]))
    assert not {"power", "cooling", "network"}.issubset(set(zrh2["completed_physical_types"]))
    assert zrh2["completed_coverage_ratio"] <= zrh2["coverage_ratio"]


def test_physical_report_exposes_evidence_and_completion_as_separate_metrics():
    events = load_event_ledger(LEDGER)
    report = physical_depth_report(events)
    assert report["projects_with_any_physical_evidence"] >= report["projects_with_any_completed_physical_type"]
    assert report["fully_mapped_projects"] >= report["fully_completed_physical_projects"]
    assert "separate" in report["interpretation"].lower()


def test_overdue_followups_preserve_unresolved_delays_instead_of_fake_actuals():
    events = load_event_ledger(LEDGER)
    for project_id in ("vantage-lhr2", "vantage-zrh2", "virtus-saunderton", "data4-hanau", "cyrusone-fra7"):
        rows = timeline(events, project_id, "operations")
        assert any(x.status == "delayed" for x in rows)
        assert not any(x.status == "actual" and x.actual_date == "2026-08-19" for x in rows)
