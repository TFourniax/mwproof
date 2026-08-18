from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from proofmw.calibration import walk_forward_interval_calibration
from proofmw.dossier import project_dossier
from proofmw.event_ledger import load_event_ledger
from proofmw.research_priority import research_priorities
from proofmw.source_watch import build_watchlist, compare_snapshots

LEDGER = ROOT / "data" / "europe-public-events-v2"


def test_interval_calibration_is_executable_but_not_overclaimed():
    events = load_event_ledger(LEDGER)
    report = walk_forward_interval_calibration(events, min_history=3)
    assert report["status"] == "SCORABLE_INTERVAL_CALIBRATION"
    assert report["resolved_examples"] >= 22
    assert report["scored_examples"] > 0
    assert "production model" in report["warning"]
    for metric in report["metrics"].values():
        if metric["n"]:
            assert 0 <= metric["coverage_lower_bound"] <= metric["coverage_upper_bound"] <= 1


def test_research_priorities_reflect_passed_diversity_gates():
    events = load_event_ledger(LEDGER)
    report = research_priorities(events)
    assert report["leading_operator"]["share"] <= 0.25
    assert report["current"]["authoritative_ratio"] >= 0.50
    assert report["gaps"]["non_leading_operator_projects_for_25pct_cap"] == 0
    assert report["gaps"]["authoritative_events_to_50pct"] == 0
    assert report["gaps"]["resolved_operations"] > 0


def test_project_dossier_preserves_revisions_and_missing_evidence():
    events = load_event_ledger(LEDGER)
    dossier = project_dossier(events, "start-campus-sines")
    assert dossier["project"]["country"] == "Portugal"
    assert dossier["evidence_summary"]["observations"] >= 6
    sin02 = next(x for x in dossier["milestones"] if x["milestone_id"] == "sin02-ready-for-service")
    assert len(sin02["target_revisions"]) >= 1
    assert "power" in dossier["evidence_summary"]["missing_physical_milestone_types"]
    assert "credit opinion" in dossier["guardrail"]


def test_project_dossier_as_of_excludes_future_evidence():
    events = load_event_ledger(LEDGER)
    dossier = project_dossier(events, "start-campus-sines", as_of="2024-12-31")
    assert all(row["observed_on"] <= "2024-12-31" for row in dossier["timeline"])


def test_watchlist_prefers_primary_sources_and_snapshot_diff_is_deterministic():
    events = load_event_ledger(LEDGER)
    watchlist = build_watchlist(events)
    assert watchlist
    assert all(row["source_class"] not in {"trade-press", "mainstream-press"} for row in watchlist)
    before = {"snapshots": [{"url": "https://example.com/a", "ok": True, "sha256": "a", "fetched_at": "t1"}]}
    after = {"snapshots": [{"url": "https://example.com/a", "ok": True, "sha256": "b", "fetched_at": "t2"}]}
    changes = compare_snapshots(before, after)
    assert len(changes) == 1
    assert changes[0]["before_sha256"] == "a"
    assert changes[0]["after_sha256"] == "b"
