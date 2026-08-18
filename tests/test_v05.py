from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from proofmw.conditional import walk_forward_conditional_benchmark
from proofmw.dataset_snapshot import dataset_snapshot
from proofmw.decision_card import project_decision_card
from proofmw.event_ledger import ledger_fingerprint, load_event_ledger
from proofmw.storage import build_sqlite_index, index_metadata, query_sqlite

LEDGER = ROOT / "data" / "europe-public-events-v2"


def test_coverage_snapshot_is_dated_hashed_and_non_overclaiming():
    events = load_event_ledger(LEDGER)
    snap = dataset_snapshot(events, as_of="2026-08-19")
    assert snap["as_of"] == "2026-08-19"
    assert snap["ledger_sha256"] == ledger_fingerprint(events)
    assert snap["scope"]["observations"] >= 150
    assert snap["scope"]["projects"] >= 68
    assert snap["scope"]["resolved_operations"] >= 25
    assert "not a claim of complete market coverage" in snap["coverage_claim"]
    assert "failed_gates" in snap["readiness"]


def test_conditional_benchmark_is_walk_forward_and_does_not_self_promote():
    events = load_event_ledger(LEDGER)
    report = walk_forward_conditional_benchmark(events, min_history=5)
    assert report["status"] == "SCORABLE_CONDITIONAL_BENCHMARK"
    assert report["scored_examples"] > 0
    assert report["metrics"]["developer_target"]["n"] == report["scored_examples"]
    assert report["metrics"]["conditional_empirical"]["n"] == report["scored_examples"]
    assert isinstance(report["comparison"]["conditional_beats_developer_on_mae"], bool)
    assert "not a production model" in report["warning"]


def test_sqlite_index_is_reproducible_and_queryable(tmp_path):
    events = load_event_ledger(LEDGER)
    path = tmp_path / "proofmw.sqlite"
    built = build_sqlite_index(events, path)
    assert built["ledger_sha256"] == ledger_fingerprint(events)
    metadata = index_metadata(path)
    assert metadata["ledger_sha256"] == built["ledger_sha256"]
    result = query_sqlite(path, country="Portugal", limit=20)
    assert result["total_matches"] > 0
    assert all(row["country"] == "Portugal" for row in result["events"])


def test_decision_card_is_lender_facing_but_evidence_only():
    events = load_event_ledger(LEDGER)
    card = project_decision_card(events, "start-campus-sines", as_of="2026-08-19")
    assert card["mode"] == "EVIDENCE_ONLY"
    assert card["evidence"]["physical_coverage_ratio"] == 1.0
    assert card["model_risk"]["publishable_levels"] == []
    assert card["next_diligence_requests"]
    assert "No automated approve/decline" in card["decision_guardrail"]


def test_new_first_party_histories_add_future_and_resolved_labels():
    events = load_event_ledger(LEDGER)
    by_project = {}
    for row in events:
        by_project.setdefault(row.project_id, []).append(row)
    for project_id in (
        "atnorth-ice03",
        "bulk-osix",
        "maincubes-ber02",
        "virtus-saunderton",
        "virtus-milan1",
    ):
        assert project_id in by_project
    assert any(
        x.project_id == "virtus-wustermark"
        and x.milestone_type == "transformer"
        and x.status == "actual"
        for x in events
    )
    assert any(
        x.project_id == "atnorth-den01"
        and x.observed_on == "2025-11-26"
        and x.status == "revised_forecast"
        for x in events
    )
